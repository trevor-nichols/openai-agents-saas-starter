"""Core façade for agent interactions.

The heavy lifting now lives in per-concern helpers under services/agents/* so
the surface here stays lean and testable.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Mapping
from datetime import datetime
from typing import Any, cast

from agents import trace

from app.api.v1.agents.schemas import AgentStatus, AgentSummary
from app.api.v1.chat.schemas import AgentChatRequest, AgentChatResponse, MessageAttachment
from app.bootstrap.container import wire_storage_service
from app.core.settings import get_settings
from app.domain.ai.lifecycle import LifecycleEventBus
from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import (
    ConversationRepository,
)
from app.guardrails._shared.events import GuardrailEmissionToken, set_guardrail_emitters
from app.services.agents.attachments import AttachmentService
from app.services.agents.catalog import AgentCatalogPage, AgentCatalogService
from app.services.agents.context import (
    ConversationActorContext,
    reset_current_actor,
    set_current_actor,
)
from app.services.agents.event_log import EventProjector
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.policy import AgentRuntimePolicy
from app.services.agents.provider_registry import AgentProviderRegistry, get_provider_registry
from app.services.agents.run_options import build_run_options
from app.services.agents.run_pipeline import (
    RunContext,
    persist_assistant_message,
    prepare_run_context,
    project_compaction_events,
    project_new_session_items,
    record_user_message,
)
from app.services.agents.session_manager import SessionManager
from app.services.agents.streaming_pipeline import (
    AgentStreamProcessor,
    GuardrailStreamForwarder,
    build_guardrail_summary,
)
from app.services.agents.usage import UsageService
from app.services.containers import (
    ContainerFilesGateway,
    ContainerService,
    OpenAIContainerFilesGateway,
)
from app.services.conversation_service import ConversationService, get_conversation_service
from app.services.storage.service import StorageService
from app.services.usage_counters import UsageCounterService, get_usage_counter_service
from app.services.usage_recorder import UsageRecorder
from app.services.vector_stores.service import VectorStoreService

logger = logging.getLogger(__name__)


class AgentService:
    """High-level façade that orchestrates agent interactions."""

    def __init__(
        self,
        *,
        conversation_repo: ConversationRepository | None = None,
        conversation_service: ConversationService | None = None,
        usage_recorder: UsageRecorder | None = None,
        usage_counter_service: UsageCounterService | None = None,
        provider_registry: AgentProviderRegistry | None = None,
        container_service: ContainerService | None = None,
        container_files_gateway: ContainerFilesGateway | None = None,
        storage_service: StorageService | None = None,
        policy: AgentRuntimePolicy | None = None,
        interaction_builder: InteractionContextBuilder | None = None,
        vector_store_service: VectorStoreService | None = None,
        session_manager: SessionManager | None = None,
        attachment_service: AttachmentService | None = None,
        usage_service: UsageService | None = None,
        catalog_service: AgentCatalogService | None = None,
    ) -> None:
        self._conversation_service = conversation_service or get_conversation_service()
        if conversation_repo is not None:
            self._conversation_service.set_repository(conversation_repo)

        self._provider_registry = provider_registry or get_provider_registry()
        self._container_service = container_service
        self._container_files_gateway = container_files_gateway
        self._storage_service = storage_service
        self._policy = policy or AgentRuntimePolicy.from_env()

        self._session_manager = session_manager or SessionManager(
            self._conversation_service, self._policy
        )
        self._attachment_service = attachment_service or AttachmentService(
            self._get_storage_service,
            container_files_gateway_resolver=self._get_container_files_gateway,
        )
        self._interaction_builder = interaction_builder or InteractionContextBuilder(
            container_service=self._container_service,
            vector_store_service=vector_store_service,
        )
        self._event_projector = EventProjector(self._conversation_service)
        self._usage_service = usage_service or UsageService(
            usage_recorder,
            usage_counter_service,
            self._conversation_service,
        )
        self._catalog_service = catalog_service or AgentCatalogService(self._provider_registry)

    async def chat(
        self, request: AgentChatRequest, *, actor: ConversationActorContext
    ) -> AgentChatResponse:
        ctx = await prepare_run_context(
            actor=actor,
            request=request,
            provider_registry=self._provider_registry,
            interaction_builder=self._interaction_builder,
            conversation_service=self._conversation_service,
            session_manager=self._session_manager,
            conversation_memory=await self._conversation_service.get_memory_config(
                request.conversation_id, tenant_id=actor.tenant_id
            )
            if request.conversation_id
            else None,
        )

        await record_user_message(
            ctx=ctx,
            request=request,
            conversation_service=self._conversation_service,
        )

        token = set_current_actor(actor)
        try:
            logger.info(
                "agent.chat.start",
                extra={
                    "tenant_id": actor.tenant_id,
                    "conversation_id": ctx.conversation_id,
                    "provider_conversation_id": ctx.provider_conversation_id,
                    "agent": ctx.descriptor.key,
                },
            )
            # For non-stream runs we keep a stable, local conversation id for trace
            # grouping. Continuation is driven by the persisted SDK session items.
            runtime_conversation_id = ctx.conversation_id
            run_options = build_run_options(request.run_options)
            if (
                run_options is not None
                and ctx.session_handle is not None
                and run_options.previous_response_id
            ):
                logger.debug(
                    "agent.chat.ignoring_previous_response_id_with_session",
                    extra={
                        "tenant_id": actor.tenant_id,
                        "conversation_id": ctx.conversation_id,
                        "agent": ctx.descriptor.key,
                    },
                )
                run_options.previous_response_id = None
            with trace(workflow_name="Agent Chat", group_id=ctx.conversation_id):
                result = await ctx.provider.runtime.run(
                    ctx.descriptor.key,
                    request.message,
                    session=ctx.session_handle,
                    conversation_id=runtime_conversation_id,
                    metadata={"prompt_runtime_ctx": ctx.runtime_ctx},
                    options=run_options,
                )
        finally:
            reset_current_actor(token)

        response_text = result.response_text or str(result.final_output)
        image_attachments = await self._attachment_service.ingest_image_outputs(
            result.tool_outputs,
            actor=actor,
            conversation_id=ctx.conversation_id,
            agent_key=ctx.descriptor.key,
            response_id=result.response_id,
        )
        container_attachments = await self._attachment_service.ingest_container_file_citations(
            result.tool_outputs,
            actor=actor,
            conversation_id=ctx.conversation_id,
            agent_key=ctx.descriptor.key,
            response_id=result.response_id,
        )
        attachments = [*image_attachments, *container_attachments]
        await persist_assistant_message(
            ctx=ctx,
            conversation_service=self._conversation_service,
            response_text=response_text,
            attachments=attachments,
            active_agent=result.final_agent,
            handoff_count=result.handoff_count,
        )
        logger.info(
            "agent.chat.end",
            extra={
                "tenant_id": actor.tenant_id,
                "conversation_id": ctx.conversation_id,
                "provider_conversation_id": ctx.provider_conversation_id,
                "agent": ctx.descriptor.key,
                "response_id": result.response_id,
            },
        )
        await self._finalize_run(
            ctx=ctx,
            tenant_id=actor.tenant_id,
            response_id=result.response_id,
            usage=result.usage,
        )

        def _resolve_output_schema(agent_key: str | None):
            if not agent_key:
                return ctx.descriptor.output_schema
            descriptor = ctx.provider.get_agent(agent_key)
            if descriptor:
                return descriptor.output_schema
            return ctx.descriptor.output_schema

        effective_schema = _resolve_output_schema(result.final_agent or ctx.descriptor.key)
        tool_overview = ctx.provider.tool_overview()
        return AgentChatResponse(
            response=response_text,
            structured_output=AgentStreamEvent._strip_unserializable(result.structured_output),
            output_schema=effective_schema,
            conversation_id=ctx.conversation_id,
            agent_used=result.final_agent or ctx.descriptor.key,
            handoff_occurred=bool(result.handoff_count),
            attachments=[
                MessageAttachment(**self._attachment_service.to_attachment_schema(att))
                for att in attachments
            ],
            metadata={
                "model_used": ctx.descriptor.model,
                "tools_available": tool_overview.get("tool_names", []),
                **self._attachment_service.attachment_metadata_note(attachments),
            },
        )

    async def chat_stream(
        self,
        request: AgentChatRequest,
        *,
        actor: ConversationActorContext,
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        lifecycle_bus = LifecycleEventBus()
        guardrail_events: list[Mapping[str, Any]] = []
        guardrail_token: GuardrailEmissionToken | None = None
        stream_handle = None

        async def _emit_compaction(event: AgentStreamEvent) -> None:
            await lifecycle_bus.emit(event)

        ctx = await prepare_run_context(
            actor=actor,
            request=request,
            provider_registry=self._provider_registry,
            interaction_builder=self._interaction_builder,
            conversation_service=self._conversation_service,
            session_manager=self._session_manager,
            conversation_memory=await self._conversation_service.get_memory_config(
                request.conversation_id, tenant_id=actor.tenant_id
            )
            if request.conversation_id
            else None,
            compaction_emitter=_emit_compaction,
        )

        processor = AgentStreamProcessor(
            lifecycle_bus=lifecycle_bus,
            provider=ctx.provider,
            actor=actor,
            conversation_id=ctx.conversation_id,
            entrypoint_agent=ctx.descriptor.key,
            entrypoint_output_schema=ctx.descriptor.output_schema,
            attachment_service=self._attachment_service,
        )

        guardrail_forwarder = GuardrailStreamForwarder(
            lifecycle_bus=lifecycle_bus,
            conversation_id=ctx.conversation_id,
            default_agent=ctx.descriptor.key,
            get_current_agent=lambda: processor.outcome.current_agent or ctx.descriptor.key,
            get_last_response_id=lambda: processor.outcome.last_response_id,
            get_fallback_response_id=(
                lambda: getattr(stream_handle, "last_response_id", None)
                if stream_handle is not None
                else None
            ),
        )
        guardrail_token = set_guardrail_emitters(
            emitter=guardrail_forwarder,
            collector=guardrail_events,
            context={
                "conversation_id": ctx.conversation_id,
                "agent": ctx.descriptor.key,
            },
        )

        await record_user_message(
            ctx=ctx,
            request=request,
            conversation_service=self._conversation_service,
        )

        token = set_current_actor(actor)
        try:
            logger.info(
                "agent.chat_stream.start",
                extra={
                    "tenant_id": actor.tenant_id,
                    "conversation_id": ctx.conversation_id,
                    "provider_conversation_id": ctx.provider_conversation_id,
                    "agent": ctx.descriptor.key,
                },
            )
            # When SDK sessions are in use, we rely on persisted session items for
            # continuation and disable provider-side conversation state to prevent
            # duplicate item ids being re-sent to the Responses API.
            runtime_conversation_id = None if ctx.session_handle is not None else (
                ctx.provider_conversation_id or ctx.conversation_id
            )
            run_options = build_run_options(request.run_options, hook_sink=lifecycle_bus)
            if (
                run_options is not None
                and ctx.session_handle is not None
                and run_options.previous_response_id
            ):
                logger.debug(
                    "agent.chat_stream.ignoring_previous_response_id_with_session",
                    extra={
                        "tenant_id": actor.tenant_id,
                        "conversation_id": ctx.conversation_id,
                        "agent": ctx.descriptor.key,
                    },
                )
                run_options.previous_response_id = None

            with trace(workflow_name="Agent Chat Stream", group_id=ctx.conversation_id):
                stream_handle = ctx.provider.runtime.run_stream(
                    ctx.descriptor.key,
                    request.message,
                    session=ctx.session_handle,
                    conversation_id=runtime_conversation_id,
                    metadata={"prompt_runtime_ctx": ctx.runtime_ctx},
                    options=run_options,
                )
                terminal_event: AgentStreamEvent | None = None
                async for event in processor.iter_events(stream_handle):
                    if event.is_terminal and event.kind != "error":
                        # Defer emitting the terminal event until after we persist the
                        # assistant message + sync session state. This keeps the public
                        # SSE `final` event aligned with durable storage and prevents
                        # client-side stream cancellation from skipping persistence.
                        terminal_event = event
                        break
                    yield event
        finally:
            reset_current_actor(token)
            if guardrail_token:
                guardrail_token.reset()

        if guardrail_events:
            summary_payload = build_guardrail_summary(guardrail_events)
            summary_event = AgentStreamEvent(
                kind="guardrail_result",
                conversation_id=ctx.conversation_id,
                agent=ctx.descriptor.key,
                guardrail_stage="summary",
                guardrail_name="Guardrail Summary",
                guardrail_key="guardrail_summary",
                guardrail_summary=True,
                payload=summary_payload,
            )
            if processor.outcome.current_output_schema is not None:
                summary_event.output_schema = processor.outcome.current_output_schema
            yield summary_event

        if terminal_event is not None and processor.pending_container_file_citations:
            container_attachments = await self._attachment_service.ingest_container_file_citations(
                processor.pending_container_file_citations,
                actor=actor,
                conversation_id=ctx.conversation_id,
                agent_key=ctx.descriptor.key,
                response_id=terminal_event.response_id
                or getattr(stream_handle, "last_response_id", None)
                if stream_handle is not None
                else None,
            )
            if container_attachments:
                processor.outcome.attachments.extend(container_attachments)
                payloads = [
                    cast(Mapping[str, Any], self._attachment_service.to_attachment_payload(att))
                    for att in container_attachments
                ]
                if terminal_event.attachments is None:
                    terminal_event.attachments = payloads
                else:
                    terminal_event.attachments.extend(payloads)

        await persist_assistant_message(
            ctx=ctx,
            conversation_service=self._conversation_service,
            response_text=processor.outcome.complete_response,
            attachments=processor.outcome.attachments,
            active_agent=processor.outcome.current_agent or ctx.descriptor.key,
            handoff_count=processor.outcome.handoff_count or None,
        )
        logger.info(
            "agent.chat_stream.end",
            extra={
                "tenant_id": actor.tenant_id,
                "conversation_id": ctx.conversation_id,
                "provider_conversation_id": ctx.provider_conversation_id,
                "agent": ctx.descriptor.key,
                "response_id": getattr(stream_handle, "last_response_id", None)
                if stream_handle is not None
                else None,
            },
        )
        await self._finalize_run(
            ctx=ctx,
            tenant_id=actor.tenant_id,
            response_id=getattr(stream_handle, "last_response_id", None)
            if stream_handle is not None
            else None,
            usage=getattr(stream_handle, "usage", None) if stream_handle is not None else None,
        )
        if terminal_event is not None:
            yield terminal_event

    @property
    def conversation_repository(self):
        """Expose the underlying repository for integration/testing scenarios."""

        return self._conversation_service.repository

    def list_available_agents(self) -> list[AgentSummary]:
        """Return the first page of the catalog using default sizing."""

        return self._catalog_service.list_available_agents()

    def list_available_agents_page(
        self, *, limit: int | None, cursor: str | None, search: str | None
    ) -> AgentCatalogPage:
        """Paginated catalog listing."""

        page = self._catalog_service.list_available_agents_page(
            limit=limit,
            cursor=cursor,
            search=search,
        )
        return page

    def get_agent_status(self, agent_name: str) -> AgentStatus:
        provider = self._get_provider()
        descriptor = provider.get_agent(agent_name)
        if not descriptor:
            raise ValueError(f"Agent '{agent_name}' not found")
        last_used = getattr(descriptor, "last_seen_at", None)
        if last_used:
            last_used = last_used.replace(microsecond=0).isoformat() + "Z"
        return AgentStatus(
            name=descriptor.key,
            status="active",
            output_schema=descriptor.output_schema,
            last_used=last_used,
            total_conversations=0,
        )

    def get_tool_information(self) -> dict[str, Any]:
        provider = self._get_provider()
        return dict(provider.tool_overview())

    def _get_provider(self):
        try:
            return self._provider_registry.get_default()
        except RuntimeError as exc:
            raise RuntimeError(
                "No agent providers registered. Register a provider (e.g., build_openai_provider)"
                " before invoking AgentService, or use the test fixture that populates the"
                " AgentProviderRegistry."
            ) from exc

    def _get_storage_service(self) -> StorageService:
        if self._storage_service is None:
            raise RuntimeError("Storage service is not configured")
        return self._storage_service

    def _get_container_files_gateway(self) -> ContainerFilesGateway:
        if self._container_files_gateway is None:
            self._container_files_gateway = OpenAIContainerFilesGateway(get_settings)
        return self._container_files_gateway

    async def _sync_session_state(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        session_id: str,
        provider_name: str | None,
        provider_conversation_id: str | None,
    ) -> None:
        await self._session_manager.sync_session_state(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            session_id=session_id,
            provider_name=provider_name,
            provider_conversation_id=provider_conversation_id,
        )

    async def _record_usage_metrics(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        response_id: str | None,
        usage: Any,
        agent_key: str | None,
        provider_name: str | None,
    ) -> None:
        await self._usage_service.record(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            response_id=response_id,
            usage=usage,
            agent_key=agent_key,
            provider=provider_name,
        )

    async def _finalize_run(
        self,
        *,
        ctx: RunContext,
        tenant_id: str,
        response_id: str | None,
        usage: Any,
    ) -> None:
        await self._sync_session_state(
            tenant_id=tenant_id,
            conversation_id=ctx.conversation_id,
            session_id=ctx.session_id,
            provider_name=ctx.provider.name,
            provider_conversation_id=ctx.provider_conversation_id,
        )
        await self._record_usage_metrics(
            tenant_id=tenant_id,
            conversation_id=ctx.conversation_id,
            response_id=response_id,
            usage=usage,
            agent_key=ctx.descriptor.key,
            provider_name=ctx.provider.name,
        )
        await project_compaction_events(
            event_projector=self._event_projector,
            compaction_events=ctx.compaction_events,
            conversation_id=ctx.conversation_id,
            tenant_id=tenant_id,
            agent=ctx.descriptor.key,
            model=ctx.descriptor.model,
            response_id=response_id,
        )
        await project_new_session_items(
            event_projector=self._event_projector,
            session_handle=ctx.session_handle,
            pre_items=ctx.pre_session_items,
            conversation_id=ctx.conversation_id,
            tenant_id=tenant_id,
            agent=ctx.descriptor.key,
            model=ctx.descriptor.model,
            response_id=response_id,
        )
        ctx.provider.mark_seen(ctx.descriptor.key, datetime.utcnow())


# Factory helpers -----------------------------------------------------------

def build_agent_service(
    *,
    conversation_service: ConversationService | None = None,
    conversation_repository: ConversationRepository | None = None,
    usage_recorder: UsageRecorder | None = None,
    usage_counter_service: UsageCounterService | None = None,
    provider_registry: AgentProviderRegistry | None = None,
    container_service: ContainerService | None = None,
    storage_service: StorageService | None = None,
    policy: AgentRuntimePolicy | None = None,
    vector_store_service: VectorStoreService | None = None,
    catalog_service: AgentCatalogService | None = None,
) -> AgentService:
    return AgentService(
        conversation_repo=conversation_repository,
        conversation_service=conversation_service,
        usage_recorder=usage_recorder,
        usage_counter_service=usage_counter_service,
        provider_registry=provider_registry,
        container_service=container_service,
        storage_service=storage_service,
        policy=policy,
        vector_store_service=vector_store_service,
        catalog_service=catalog_service,
    )


def get_agent_service() -> AgentService:
    from app.bootstrap.container import get_container
    from app.infrastructure.db import get_async_sessionmaker

    container = get_container()
    if container.session_factory is None:
        container.session_factory = get_async_sessionmaker()
    if container.agent_service is None:
        if container.storage_service is None:
            wire_storage_service(container)
        container.agent_service = build_agent_service(
            conversation_service=container.conversation_service,
            conversation_repository=None,
            usage_recorder=container.usage_recorder,
            usage_counter_service=get_usage_counter_service(),
            provider_registry=get_provider_registry(),
            container_service=container.container_service,
            storage_service=container.storage_service,
            vector_store_service=container.vector_store_service,
        )
    return container.agent_service


class _AgentServiceHandle:
    def __getattr__(self, name: str):
        return getattr(get_agent_service(), name)

    def __setattr__(self, name: str, value):
        setattr(get_agent_service(), name, value)

    def __delattr__(self, name: str):
        delattr(get_agent_service(), name)


agent_service = _AgentServiceHandle()


__all__ = [
    "AgentService",
    "ConversationActorContext",
    "agent_service",
    "build_agent_service",
    "get_agent_service",
]
