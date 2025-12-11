"""Core façade for agent interactions.

The heavy lifting now lives in per-concern helpers under services/agents/* so
the surface here stays lean and testable.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator, Mapping
from datetime import datetime
from typing import Any

from agents import trace

from app.api.v1.agents.schemas import AgentStatus, AgentSummary
from app.api.v1.chat.schemas import AgentChatRequest, AgentChatResponse, MessageAttachment
from app.bootstrap.container import wire_storage_service, wire_title_service
from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import (
    ConversationAttachment,
    ConversationMessage,
    ConversationRepository,
)
from app.guardrails._shared.events import GuardrailEmissionToken, set_guardrail_emitters
from app.infrastructure.providers.openai.runtime import LifecycleEventBus
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
    build_metadata,
    persist_assistant_message,
    prepare_run_context,
    project_new_session_items,
    record_user_message,
)
from app.services.agents.session_manager import SessionManager
from app.services.agents.usage import UsageService
from app.services.containers import ContainerService
from app.services.conversation_service import ConversationService, get_conversation_service
from app.services.conversations.title_service import TitleService
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
        storage_service: StorageService | None = None,
        policy: AgentRuntimePolicy | None = None,
        interaction_builder: InteractionContextBuilder | None = None,
        vector_store_service: VectorStoreService | None = None,
        session_manager: SessionManager | None = None,
        attachment_service: AttachmentService | None = None,
        usage_service: UsageService | None = None,
        catalog_service: AgentCatalogService | None = None,
        title_service: TitleService | None = None,
    ) -> None:
        self._conversation_service = conversation_service or get_conversation_service()
        if conversation_repo is not None:
            self._conversation_service.set_repository(conversation_repo)

        self._provider_registry = provider_registry or get_provider_registry()
        self._container_service = container_service
        self._storage_service = storage_service
        self._policy = policy or AgentRuntimePolicy.from_env()

        self._session_manager = session_manager or SessionManager(
            self._conversation_service, self._policy
        )
        self._attachment_service = attachment_service or AttachmentService(
            self._get_storage_service
        )
        self._interaction_builder = interaction_builder or InteractionContextBuilder(
            container_service=self._container_service,
            vector_store_service=vector_store_service,
        )
        self._event_projector = EventProjector(self._conversation_service)
        self._usage_service = usage_service or UsageService(
            usage_recorder,
            usage_counter_service or get_usage_counter_service(),
            self._conversation_service,
        )
        self._catalog_service = catalog_service or AgentCatalogService(self._provider_registry)
        self._title_service = title_service

    def _start_title_task(
        self,
        *,
        is_new_conversation: bool,
        conversation_id: str,
        tenant_id: str,
        first_user_message: str,
    ) -> asyncio.Task[str | None] | None:
        if not self._title_service or not is_new_conversation:
            return None
        return asyncio.create_task(
            self._title_service.generate_if_absent(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                first_user_message=first_user_message,
            )
        )

    @staticmethod
    def _attach_error_logger(
        task: asyncio.Task[str | None] | None, *, context: dict[str, object]
    ) -> None:
        if task is None:
            return

        def _log_failure(t: asyncio.Task[str | None]) -> None:
            if t.cancelled():
                return
            exc = t.exception()
            if exc:
                logger.exception("title_generation.task_failed", extra=context, exc_info=exc)

        task.add_done_callback(_log_failure)

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
        title_task = self._start_title_task(
            is_new_conversation=ctx.existing_state is None,
            conversation_id=ctx.conversation_id,
            tenant_id=actor.tenant_id,
            first_user_message=request.message,
        )
        self._attach_error_logger(
            title_task,
            context={
                "conversation_id": ctx.conversation_id,
                "tenant_id": actor.tenant_id,
            },
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
            runtime_conversation_id = ctx.provider_conversation_id or ctx.conversation_id
            with trace(workflow_name="Agent Chat", group_id=ctx.conversation_id):
                result = await ctx.provider.runtime.run(
                    ctx.descriptor.key,
                    request.message,
                    session=ctx.session_handle,
                    conversation_id=runtime_conversation_id,
                    metadata={"prompt_runtime_ctx": ctx.runtime_ctx},
                    options=build_run_options(request.run_options),
                )
        finally:
            reset_current_actor(token)

        response_text = result.response_text or str(result.final_output)
        attachments = await self._attachment_service.ingest_image_outputs(
            result.tool_outputs,
            actor=actor,
            conversation_id=ctx.conversation_id,
            agent_key=ctx.descriptor.key,
            response_id=result.response_id,
        )
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
        await self._sync_session_state(
            tenant_id=actor.tenant_id,
            conversation_id=ctx.conversation_id,
            session_id=ctx.session_id,
            provider_name=ctx.provider.name,
            provider_conversation_id=ctx.provider_conversation_id,
        )
        await self._record_usage_metrics(
            tenant_id=actor.tenant_id,
            conversation_id=ctx.conversation_id,
            response_id=result.response_id,
            usage=result.usage,
            agent_key=ctx.descriptor.key,
            provider_name=ctx.provider.name,
        )

        if ctx.compaction_events:
            try:
                await self._event_projector.ingest_session_items(
                    conversation_id=ctx.conversation_id,
                    tenant_id=actor.tenant_id,
                    session_items=
                    [AgentStreamEvent._to_mapping(ev) or {} for ev in ctx.compaction_events],
                    agent=ctx.descriptor.key,
                    model=ctx.descriptor.model,
                    response_id=result.response_id,
                )
            except Exception:  # pragma: no cover - defensive
                logger.exception(
                    "compaction_event_projection_failed",
                    extra={
                        "conversation_id": ctx.conversation_id,
                        "tenant_id": actor.tenant_id,
                    },
                )

        await project_new_session_items(
            event_projector=self._event_projector,
            session_handle=ctx.session_handle,
            pre_items=ctx.pre_session_items,
            conversation_id=ctx.conversation_id,
            tenant_id=actor.tenant_id,
            agent=ctx.descriptor.key,
            model=ctx.descriptor.model,
            response_id=result.response_id,
        )

        ctx.provider.mark_seen(ctx.descriptor.key, datetime.utcnow())

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
        compaction_events: list[AgentStreamEvent] = []
        guardrail_events: list[Mapping[str, Any]] = []
        guardrail_token: GuardrailEmissionToken | None = None
        last_response_id: str | None = None

        async def _emit_compaction(event: AgentStreamEvent) -> None:
            await lifecycle_bus.emit(event)
            compaction_events.append(event)

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
        current_agent = ctx.descriptor.key
        current_output_schema = ctx.descriptor.output_schema

        def _emit_guardrail(payload: Mapping[str, Any]) -> None:
            fallback_response_id = None
            try:
                if stream_handle is not None:
                    fallback_response_id = getattr(stream_handle, "last_response_id", None)
            except Exception:
                fallback_response_id = None

            response_id = payload.get("response_id") or last_response_id or fallback_response_id
            agent_for_event = payload.get("agent") or current_agent or ctx.descriptor.key
            event = AgentStreamEvent(
                kind="guardrail_result",
                conversation_id=ctx.conversation_id,
                agent=agent_for_event,
                response_id=response_id,
                guardrail_stage=payload.get("guardrail_stage"),
                guardrail_key=payload.get("guardrail_key"),
                guardrail_name=payload.get("guardrail_name"),
                guardrail_tripwire_triggered=payload.get("guardrail_tripwire_triggered"),
                guardrail_suppressed=payload.get("guardrail_suppressed"),
                guardrail_flagged=payload.get("guardrail_flagged"),
                guardrail_confidence=payload.get("guardrail_confidence"),
                guardrail_masked_content=payload.get("guardrail_masked_content"),
                guardrail_token_usage=payload.get("guardrail_token_usage"),
                guardrail_details=payload.get("guardrail_details"),
                tool_name=payload.get("tool_name"),
                tool_call_id=payload.get("tool_call_id"),
                payload=(
                    payload.get("payload")
                    if isinstance(payload.get("payload"), Mapping)
                    else None
                ),
            )
            try:
                loop = asyncio.get_running_loop()
                lifecycle_emit_task = loop.create_task(lifecycle_bus.emit(event))
                lifecycle_emit_task.add_done_callback(lambda _: None)
            except Exception:
                logger.exception(
                    "guardrail_event.emit_failed",
                    extra={"stage": payload.get("guardrail_stage")},
                )

        guardrail_token = set_guardrail_emitters(
            emitter=_emit_guardrail,
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
        title_task = self._start_title_task(
            is_new_conversation=ctx.existing_state is None,
            conversation_id=ctx.conversation_id,
            tenant_id=actor.tenant_id,
            first_user_message=request.message,
        )
        self._attach_error_logger(
            title_task,
            context={
                "conversation_id": ctx.conversation_id,
                "tenant_id": actor.tenant_id,
            },
        )

        complete_response = ""
        attachments: list[ConversationAttachment] = []
        seen_tool_calls: set[str] = set()
        handoff_count = 0
        token = set_current_actor(actor)
        stream_handle = None
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
            # Disable provider-side conversation state when sessions are in use to
            # prevent duplicate items being sent (Responses API 400 on duplicate ids).
            runtime_conversation_id = None

            with trace(workflow_name="Agent Chat Stream", group_id=ctx.conversation_id):
                stream_handle = ctx.provider.runtime.run_stream(
                    ctx.descriptor.key,
                    request.message,
                    session=ctx.session_handle,
                    conversation_id=runtime_conversation_id,
                    metadata={"prompt_runtime_ctx": ctx.runtime_ctx},
                    options=build_run_options(request.run_options, hook_sink=lifecycle_bus),
                )
                async for event in stream_handle.events():
                    event.conversation_id = ctx.conversation_id
                    if event.agent is None:
                        event.agent = ctx.descriptor.key

                    if event.response_id:
                        last_response_id = event.response_id

                    if event.text_delta:
                        complete_response += event.text_delta
                    elif event.response_text and not complete_response:
                        complete_response = event.response_text

                    attachment_sources: list[Mapping[str, Any]] = []
                    if event.payload and isinstance(event.payload, Mapping):
                        attachment_sources.append(event.payload)
                    if isinstance(event.tool_call, Mapping):
                        attachment_sources.append(event.tool_call)

                    new_attachments = await self._attachment_service.ingest_image_outputs(
                        attachment_sources or None,
                        actor=actor,
                        conversation_id=ctx.conversation_id,
                        agent_key=ctx.descriptor.key,
                        response_id=event.response_id,
                        seen_tool_calls=seen_tool_calls,
                    )
                    if new_attachments:
                        attachments.extend(new_attachments)
                        event.attachments = [
                            self._attachment_service.to_attachment_payload(att)
                            for att in new_attachments
                        ]
                        if event.payload is None:
                            event.payload = {}
                        if isinstance(event.payload, dict):
                            event.payload.setdefault("_attachment_note", "stored")

                    if event.kind == "agent_updated_stream_event":
                        if event.new_agent:
                            current_agent = event.new_agent
                            descriptor = ctx.provider.get_agent(current_agent)
                            if descriptor:
                                current_output_schema = descriptor.output_schema
                        handoff_count += 1

                    # Ensure stream payloads are JSON-serializable for SSE.
                    event.payload = AgentStreamEvent._strip_unserializable(event.payload)
                    event.structured_output = AgentStreamEvent._strip_unserializable(
                        event.structured_output
                    )
                    event.response_text = (
                        None if event.response_text is None else str(event.response_text)
                    )
                    if event.output_schema is None and current_output_schema is not None:
                        event.output_schema = current_output_schema

                    yield event

                    if event.is_terminal:
                        break
                async for leftover in lifecycle_bus.drain():
                    leftover.conversation_id = ctx.conversation_id
                    if leftover.output_schema is None and current_output_schema is not None:
                        leftover.output_schema = current_output_schema
                    yield leftover
            if stream_handle is not None and hasattr(stream_handle, "last_response_id"):
                last_response_id = last_response_id or getattr(
                    stream_handle, "last_response_id", None
                )
        finally:
            reset_current_actor(token)
            if guardrail_token:
                guardrail_token.reset()

        if guardrail_events:
            summary_payload = self._build_guardrail_summary(guardrail_events)
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
            if current_output_schema is not None:
                summary_event.output_schema = current_output_schema
            yield summary_event

        assistant_message = ConversationMessage(
            role="assistant",
            content=complete_response,
            attachments=attachments,
        )
        await self._conversation_service.append_message(
            ctx.conversation_id,
            assistant_message,
            tenant_id=actor.tenant_id,
            metadata=build_metadata(
                tenant_id=actor.tenant_id,
                provider=ctx.provider.name,
                provider_conversation_id=ctx.provider_conversation_id,
                agent_entrypoint=request.agent_type or ctx.descriptor.key,
                active_agent=current_agent,
                session_id=ctx.session_id,
                user_id=actor.user_id,
                handoff_count=handoff_count or None,
            ),
        )
        logger.info(
            "agent.chat_stream.end",
            extra={
                "tenant_id": actor.tenant_id,
                "conversation_id": ctx.conversation_id,
                "provider_conversation_id": ctx.provider_conversation_id,
                "agent": ctx.descriptor.key,
                "response_id": getattr(stream_handle, "last_response_id", None),
            },
        )
        await self._sync_session_state(
            tenant_id=actor.tenant_id,
            conversation_id=ctx.conversation_id,
            session_id=ctx.session_id,
            provider_name=ctx.provider.name,
            provider_conversation_id=ctx.provider_conversation_id,
        )
        await self._record_usage_metrics(
            tenant_id=actor.tenant_id,
            conversation_id=ctx.conversation_id,
            response_id=getattr(stream_handle, "last_response_id", None),
            usage=getattr(stream_handle, "usage", None),
            agent_key=ctx.descriptor.key,
            provider_name=ctx.provider.name,
        )

        if ctx.compaction_events:
            try:
                await self._event_projector.ingest_session_items(
                    conversation_id=ctx.conversation_id,
                    tenant_id=actor.tenant_id,
                    session_items=
                    [AgentStreamEvent._to_mapping(ev) or {} for ev in ctx.compaction_events],
                    agent=ctx.descriptor.key,
                    model=ctx.descriptor.model,
                    response_id=getattr(stream_handle, "last_response_id", None),
                )
            except Exception:  # pragma: no cover - defensive
                logger.exception(
                    "compaction_event_projection_failed",
                    extra={
                        "conversation_id": ctx.conversation_id,
                        "tenant_id": actor.tenant_id,
                    },
                )

        await project_new_session_items(
            event_projector=self._event_projector,
            session_handle=ctx.session_handle,
            pre_items=ctx.pre_session_items,
            conversation_id=ctx.conversation_id,
            tenant_id=actor.tenant_id,
            agent=ctx.descriptor.key,
            model=ctx.descriptor.model,
            response_id=getattr(stream_handle, "last_response_id", None),
        )

        ctx.provider.mark_seen(ctx.descriptor.key, datetime.utcnow())

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

    @staticmethod
    def _build_guardrail_summary(events: list[Mapping[str, Any]]) -> dict[str, Any]:
        total = len(events)
        triggered = sum(1 for ev in events if ev.get("guardrail_tripwire_triggered"))
        suppressed = sum(
            1
            for ev in events
            if ev.get("guardrail_tripwire_triggered") and ev.get("guardrail_suppressed")
        )

        by_stage: dict[str, dict[str, int]] = {}
        by_key: dict[str, int] = {}
        usage_totals: dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        usage_found = False

        for ev in events:
            stage = ev.get("guardrail_stage") or "unknown"
            stage_bucket = by_stage.setdefault(stage, {"total": 0, "triggered": 0})
            stage_bucket["total"] += 1
            if ev.get("guardrail_tripwire_triggered"):
                stage_bucket["triggered"] += 1

            key = ev.get("guardrail_key")
            if key:
                by_key[key] = by_key.get(key, 0) + 1

            token_usage = ev.get("guardrail_token_usage")
            if isinstance(token_usage, dict):
                seen_usage = False
                for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
                    value = token_usage.get(field)
                    if isinstance(value, int):
                        usage_totals[field] = usage_totals.get(field, 0) + value
                        seen_usage = True
                if seen_usage:
                    usage_found = True

        summary = {
            "total": total,
            "triggered": triggered,
            "suppressed": suppressed,
            "by_stage": by_stage,
            "by_key": by_key,
        }
        if usage_found:
            summary["token_usage"] = usage_totals

        return summary


# Factory helpers -----------------------------------------------------------

def build_agent_service(
    *,
    conversation_service: ConversationService | None = None,
    conversation_repository: ConversationRepository | None = None,
    usage_recorder: UsageRecorder | None = None,
    provider_registry: AgentProviderRegistry | None = None,
    container_service: ContainerService | None = None,
    storage_service: StorageService | None = None,
    policy: AgentRuntimePolicy | None = None,
    vector_store_service: VectorStoreService | None = None,
    catalog_service: AgentCatalogService | None = None,
    title_service: TitleService | None = None,
) -> AgentService:
    return AgentService(
        conversation_repo=conversation_repository,
        conversation_service=conversation_service,
        usage_recorder=usage_recorder,
        provider_registry=provider_registry,
        container_service=container_service,
        storage_service=storage_service,
        policy=policy,
        vector_store_service=vector_store_service,
        catalog_service=catalog_service,
        title_service=title_service,
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
        wire_title_service(container)
        container.agent_service = build_agent_service(
            conversation_service=container.conversation_service,
            conversation_repository=None,
            usage_recorder=container.usage_recorder,
            provider_registry=get_provider_registry(),
            container_service=container.container_service,
            storage_service=container.storage_service,
            vector_store_service=container.vector_store_service,
            title_service=container.title_service,
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
