"""Core façade for agent interactions.

This module now delegates discrete responsibilities to specialized helpers to
keep the public API stable while making the orchestration testable and
maintainable.
"""

from __future__ import annotations

import inspect
import logging
import uuid
from collections.abc import AsyncGenerator, Iterable
from typing import Any

from agents import trace

from app.api.v1.agents.schemas import AgentStatus, AgentSummary
from app.api.v1.chat.schemas import AgentChatRequest, AgentChatResponse, MessageAttachment
from app.api.v1.conversations.schemas import ConversationHistory, ConversationSummary
from app.bootstrap.container import get_container, wire_storage_service
from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import (
    ConversationAttachment,
    ConversationEvent,
    ConversationMessage,
    ConversationMetadata,
    ConversationRepository,
)
from app.infrastructure.providers.openai.runtime import LifecycleEventBus
from app.services.agents.attachments import AttachmentService
from app.services.agents.context import (
    ConversationActorContext,
    reset_current_actor,
    set_current_actor,
)
from app.services.agents.event_log import EventProjector
from app.services.agents.history import ConversationHistoryService
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.policy import AgentRuntimePolicy
from app.services.agents.provider_registry import AgentProviderRegistry, get_provider_registry
from app.services.agents.session_manager import SessionManager
from app.services.agents.usage import UsageService
from app.services.containers import ContainerService, get_container_service
from app.services.conversation_service import (
    ConversationService,
    SearchResult,
    get_conversation_service,
)
from app.services.storage.service import StorageService
from app.services.usage_recorder import UsageRecorder

logger = logging.getLogger(__name__)


class AgentService:
    """High-level façade that orchestrates agent interactions."""

    def __init__(
        self,
        *,
        conversation_repo: ConversationRepository | None = None,
        conversation_service: ConversationService | None = None,
        usage_recorder: UsageRecorder | None = None,
        provider_registry: AgentProviderRegistry | None = None,
        container_service: ContainerService | None = None,
        storage_service: StorageService | None = None,
        policy: AgentRuntimePolicy | None = None,
        interaction_builder: InteractionContextBuilder | None = None,
        session_manager: SessionManager | None = None,
        attachment_service: AttachmentService | None = None,
        history_service: ConversationHistoryService | None = None,
        usage_service: UsageService | None = None,
    ) -> None:
        self._conversation_service = conversation_service or get_conversation_service()
        if conversation_repo is not None:
            self._conversation_service.set_repository(conversation_repo)

        self._provider_registry = provider_registry or get_provider_registry()
        self._container_service = container_service or get_container_service()
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
        )
        self._history_service = history_service or ConversationHistoryService(
            self._conversation_service,
            self._attachment_service,
        )
        self._event_projector = EventProjector(self._conversation_service)
        self._usage_service = usage_service or UsageService(usage_recorder)

    async def chat(
        self, request: AgentChatRequest, *, actor: ConversationActorContext
    ) -> AgentChatResponse:
        provider = self._get_provider()
        descriptor = provider.resolve_agent(request.agent_type)
        conversation_id = request.conversation_id or str(uuid.uuid4())

        runtime_ctx = await self._interaction_builder.build(
            actor=actor, request=request, conversation_id=conversation_id
        )
        existing_state = await self._conversation_service.get_session_state(
            conversation_id, tenant_id=actor.tenant_id
        )
        # When using SDK sessions, do not also send provider conversation_id to avoid
        # double-feeding history (Responses API would see duplicates). Keep server
        # state off and rely on session_store only.
        provider_conversation_id = None
        session_id, session_handle = await self._session_manager.acquire_session(
            provider,
            actor.tenant_id,
            conversation_id,
            provider_conversation_id,
        )

        pre_session_items = await self._get_session_items(session_handle)

        user_message = ConversationMessage(role="user", content=request.message)
        await self._conversation_service.append_message(
            conversation_id,
            user_message,
            tenant_id=actor.tenant_id,
            metadata=self._build_metadata(
                tenant_id=actor.tenant_id,
                provider=provider.name,
                provider_conversation_id=None,
                agent_entrypoint=request.agent_type or descriptor.key,
                active_agent=descriptor.key,
                session_id=session_id,
                user_id=actor.user_id,
            ),
        )
        await self._conversation_service.record_conversation_created(
            conversation_id,
            tenant_id=actor.tenant_id,
            agent_entrypoint=request.agent_type or descriptor.key,
            existed=existing_state is not None,
        )

        token = set_current_actor(actor)
        try:
            logger.info(
                "agent.chat.start",
                extra={
                    "tenant_id": actor.tenant_id,
                    "conversation_id": conversation_id,
                    "provider_conversation_id": provider_conversation_id,
                    "agent": descriptor.key,
                },
            )
            runtime_conversation_id = (
                provider_conversation_id if provider_conversation_id else conversation_id
            )
            run_options = None
            with trace(workflow_name="Agent Chat", group_id=conversation_id):
                result = await provider.runtime.run(
                    descriptor.key,
                    request.message,
                    session=session_handle,
                    conversation_id=runtime_conversation_id,
                    metadata={"prompt_runtime_ctx": runtime_ctx},
                    options=run_options,
                )
        finally:
            reset_current_actor(token)

        response_text = result.response_text or str(result.final_output)
        attachments = await self._attachment_service.ingest_image_outputs(
            result.tool_outputs,
            actor=actor,
            conversation_id=conversation_id,
            agent_key=descriptor.key,
            response_id=result.response_id,
        )
        assistant_message = ConversationMessage(
            role="assistant",
            content=response_text,
            attachments=attachments,
        )
        await self._conversation_service.append_message(
            conversation_id,
            assistant_message,
            tenant_id=actor.tenant_id,
            metadata=self._build_metadata(
                tenant_id=actor.tenant_id,
                provider=provider.name,
                provider_conversation_id=None,
                agent_entrypoint=request.agent_type or descriptor.key,
                active_agent=descriptor.key,
                session_id=session_id,
                user_id=actor.user_id,
            ),
        )
        logger.info(
            "agent.chat.end",
            extra={
                "tenant_id": actor.tenant_id,
                "conversation_id": conversation_id,
                "provider_conversation_id": provider_conversation_id,
                "agent": descriptor.key,
                "response_id": result.response_id,
            },
        )
        await self._sync_session_state(
            tenant_id=actor.tenant_id,
            conversation_id=conversation_id,
            session_id=session_id,
            provider_name=provider.name,
            provider_conversation_id=None,
        )
        await self._record_usage_metrics(
            tenant_id=actor.tenant_id,
            conversation_id=conversation_id,
            response_id=result.response_id,
            usage=result.usage,
        )

        await self._ingest_new_session_items(
            session_handle=session_handle,
            pre_items=pre_session_items,
            conversation_id=conversation_id,
            tenant_id=actor.tenant_id,
            agent=descriptor.key,
            model=descriptor.model,
            response_id=result.response_id,
        )

        tool_overview = provider.tool_overview()
        return AgentChatResponse(
            response=response_text,
            structured_output=AgentStreamEvent._strip_unserializable(result.structured_output),
            conversation_id=conversation_id,
            agent_used=descriptor.key,
            handoff_occurred=False,
            attachments=[
                MessageAttachment(**self._attachment_service.to_attachment_schema(att))
                for att in attachments
            ],
            metadata={
                "model_used": descriptor.model,
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
        provider = self._get_provider()
        descriptor = provider.resolve_agent(request.agent_type)
        conversation_id = request.conversation_id or str(uuid.uuid4())

        runtime_ctx = await self._interaction_builder.build(
            actor=actor, request=request, conversation_id=conversation_id
        )
        existing_state = await self._conversation_service.get_session_state(
            conversation_id, tenant_id=actor.tenant_id
        )
        # Use SDK session memory only; avoid provider-side conversation ids to prevent
        # duplicate item errors from the Responses API.
        provider_conversation_id = None
        session_id, session_handle = await self._session_manager.acquire_session(
            provider,
            actor.tenant_id,
            conversation_id,
            provider_conversation_id,
        )

        pre_session_items = await self._get_session_items(session_handle)

        user_message = ConversationMessage(role="user", content=request.message)
        await self._conversation_service.append_message(
            conversation_id,
            user_message,
            tenant_id=actor.tenant_id,
            metadata=self._build_metadata(
                tenant_id=actor.tenant_id,
                provider=provider.name,
                provider_conversation_id=None,
                agent_entrypoint=request.agent_type or descriptor.key,
                active_agent=descriptor.key,
                session_id=session_id,
                user_id=actor.user_id,
            ),
        )
        await self._conversation_service.record_conversation_created(
            conversation_id,
            tenant_id=actor.tenant_id,
            agent_entrypoint=request.agent_type or descriptor.key,
            existed=existing_state is not None,
        )

        complete_response = ""
        attachments: list[ConversationAttachment] = []
        seen_tool_calls: set[str] = set()
        token = set_current_actor(actor)
        stream_handle = None
        try:
            logger.info(
                "agent.chat_stream.start",
                extra={
                    "tenant_id": actor.tenant_id,
                    "conversation_id": conversation_id,
                    "provider_conversation_id": provider_conversation_id,
                    "agent": descriptor.key,
                },
            )
            runtime_conversation_id = provider_conversation_id if provider_conversation_id else None
            # Disable provider-side conversation state when sessions are in use to
            # prevent duplicate items being sent (Responses API 400 on duplicate ids).
            runtime_conversation_id = None

            lifecycle_bus = LifecycleEventBus()
            run_options = None
            with trace(workflow_name="Agent Chat Stream", group_id=conversation_id):
                stream_handle = provider.runtime.run_stream(
                    descriptor.key,
                    request.message,
                    session=session_handle,
                    conversation_id=runtime_conversation_id,
                    metadata={"prompt_runtime_ctx": runtime_ctx},
                    options=run_options,
                )
                async for event in stream_handle.events():
                    event.conversation_id = conversation_id
                    if event.agent is None:
                        event.agent = descriptor.key

                    if event.text_delta:
                        complete_response += event.text_delta
                    elif event.response_text and not complete_response:
                        complete_response = event.response_text

                    new_attachments = await self._attachment_service.ingest_image_outputs(
                        [event.payload] if event.payload else None,
                        actor=actor,
                        conversation_id=conversation_id,
                        agent_key=descriptor.key,
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

                    # Ensure stream payloads are JSON-serializable for SSE.
                    event.payload = AgentStreamEvent._strip_unserializable(event.payload)
                    event.structured_output = AgentStreamEvent._strip_unserializable(
                        event.structured_output
                    )
                    event.response_text = (
                        None if event.response_text is None else str(event.response_text)
                    )

                    yield event

                    if event.is_terminal:
                        break
                async for leftover in lifecycle_bus.drain():
                    leftover.conversation_id = conversation_id
                    yield leftover
        finally:
            reset_current_actor(token)

        assistant_message = ConversationMessage(
            role="assistant",
            content=complete_response,
            attachments=attachments,
        )
        await self._conversation_service.append_message(
            conversation_id,
            assistant_message,
            tenant_id=actor.tenant_id,
            metadata=self._build_metadata(
                tenant_id=actor.tenant_id,
                provider=provider.name,
                provider_conversation_id=provider_conversation_id,
                agent_entrypoint=request.agent_type or descriptor.key,
                active_agent=descriptor.key,
                session_id=session_id,
                user_id=actor.user_id,
            ),
        )
        logger.info(
            "agent.chat_stream.end",
            extra={
                "tenant_id": actor.tenant_id,
                "conversation_id": conversation_id,
                "provider_conversation_id": provider_conversation_id,
                "agent": descriptor.key,
                "response_id": getattr(stream_handle, "last_response_id", None),
            },
        )
        await self._sync_session_state(
            tenant_id=actor.tenant_id,
            conversation_id=conversation_id,
            session_id=session_id,
            provider_name=provider.name,
            provider_conversation_id=None,
        )
        await self._record_usage_metrics(
            tenant_id=actor.tenant_id,
            conversation_id=conversation_id,
            response_id=getattr(stream_handle, "last_response_id", None),
            usage=getattr(stream_handle, "usage", None),
        )

        await self._ingest_new_session_items(
            session_handle=session_handle,
            pre_items=pre_session_items,
            conversation_id=conversation_id,
            tenant_id=actor.tenant_id,
            agent=descriptor.key,
            model=descriptor.model,
            response_id=getattr(stream_handle, "last_response_id", None),
        )

    async def get_conversation_history(
        self, conversation_id: str, *, actor: ConversationActorContext
    ) -> ConversationHistory:
        return await self._history_service.get_history(conversation_id, actor=actor)

    async def get_conversation_events(
        self,
        conversation_id: str,
        *,
        actor: ConversationActorContext,
        workflow_run_id: str | None = None,
    ) -> list[ConversationEvent]:
        events = await self._conversation_service.get_run_events(
            conversation_id,
            tenant_id=actor.tenant_id,
            workflow_run_id=workflow_run_id,
        )
        return events

    async def list_conversations(
        self,
        *,
        actor: ConversationActorContext,
        limit: int = 50,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
        updated_after: Any | None = None,
    ) -> tuple[list[ConversationSummary], str | None]:
        return await self._history_service.list_summaries(
            actor=actor,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent_entrypoint,
            updated_after=updated_after,
        )

    async def search_conversations(
        self,
        *,
        actor: ConversationActorContext,
        query: str,
        limit: int = 20,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
    ) -> tuple[list[SearchResult], str | None]:
        return await self._history_service.search(
            actor=actor,
            query=query,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent_entrypoint,
        )

    async def clear_conversation(
        self,
        conversation_id: str,
        *,
        actor: ConversationActorContext,
    ) -> None:
        await self._history_service.clear(conversation_id, actor=actor)

    @property
    def conversation_repository(self):
        """Expose the underlying repository for integration/testing scenarios."""

        return self._conversation_service.repository

    def list_available_agents(self) -> list[AgentSummary]:
        provider = self._get_provider()
        return [
            AgentSummary(
                name=descriptor.key,
                status=descriptor.status,
                description=descriptor.description,
            )
            for descriptor in provider.list_agents()
        ]

    def get_agent_status(self, agent_name: str) -> AgentStatus:
        provider = self._get_provider()
        descriptor = provider.get_agent(agent_name)
        if not descriptor:
            raise ValueError(f"Agent '{agent_name}' not found")
        return AgentStatus(
            name=descriptor.key,
            status="active",
            last_used=None,
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
            container = get_container()
            if container.storage_service is None:
                wire_storage_service(container)
            self._storage_service = container.storage_service
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
    ) -> None:
        await self._usage_service.record(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            response_id=response_id,
            usage=usage,
        )

    async def _get_session_items(self, session_handle: Any) -> list[dict[str, Any]]:
        getter = getattr(session_handle, "get_items", None)
        if getter is None or not callable(getter):
            return []
        try:
            result = getter()
            items = await result if inspect.isawaitable(result) else result
            if items is None or not isinstance(items, Iterable):
                return []
            return list(items)
        except Exception:
            logger.exception("Failed to fetch session items; continuing without projection")
            return []

    async def _ingest_new_session_items(
        self,
        *,
        session_handle: Any,
        pre_items: list[dict[str, Any]],
        conversation_id: str,
        tenant_id: str,
        agent: str | None,
        model: str | None,
        response_id: str | None,
        workflow_run_id: str | None = None,
    ) -> None:
        post_items = await self._get_session_items(session_handle)
        if not post_items:
            return
        delta = post_items[len(pre_items) :]
        if not delta:
            return
        try:
            await self._event_projector.ingest_session_items(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                session_items=delta,
                agent=agent,
                model=model,
                response_id=response_id,
                workflow_run_id=workflow_run_id,
            )
        except Exception:
            logger.exception(
                "event_projection_failed",
                extra={
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "agent": agent,
                },
            )
            # Best-effort: do not fail the chat flow if telemetry ingestion breaks.

    @staticmethod
    def _build_metadata(
        *,
        tenant_id: str,
        provider: str | None,
        provider_conversation_id: str | None,
        agent_entrypoint: str,
        active_agent: str,
        session_id: str,
        user_id: str,
    ) -> ConversationMetadata:
        return ConversationMetadata(
            tenant_id=tenant_id,
            provider=provider,
            provider_conversation_id=provider_conversation_id,
            agent_entrypoint=agent_entrypoint,
            active_agent=active_agent,
            sdk_session_id=session_id,
            user_id=user_id,
        )


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
) -> AgentService:
    return AgentService(
        conversation_repo=conversation_repository,
        conversation_service=conversation_service,
        usage_recorder=usage_recorder,
        provider_registry=provider_registry,
        container_service=container_service,
        storage_service=storage_service,
        policy=policy,
    )


def get_agent_service() -> AgentService:
    from app.bootstrap.container import get_container

    container = get_container()
    if container.agent_service is None:
        container.agent_service = build_agent_service(
            conversation_service=container.conversation_service,
            conversation_repository=None,
            usage_recorder=container.usage_recorder,
            provider_registry=get_provider_registry(),
            container_service=container.container_service,
            storage_service=container.storage_service,
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
