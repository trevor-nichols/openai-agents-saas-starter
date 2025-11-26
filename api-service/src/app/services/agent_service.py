"""Core agent orchestration services."""

from __future__ import annotations

import logging
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from agents import trace

from app.agents._shared.prompt_context import PromptRuntimeContext
from app.api.v1.agents.schemas import AgentStatus, AgentSummary
from app.api.v1.chat.schemas import AgentChatRequest, AgentChatResponse
from app.api.v1.conversations.schemas import ChatMessage, ConversationHistory, ConversationSummary
from app.core.config import get_settings
from app.domain.ai import AgentRunUsage, RunOptions
from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import (
    ConversationMessage,
    ConversationMetadata,
    ConversationRepository,
    ConversationSessionState,
)
from app.infrastructure.providers.openai.runtime import LifecycleEventBus
from app.services.agents.context import (
    ConversationActorContext,
    reset_current_actor,
    set_current_actor,
)
from app.services.agents.provider_registry import (
    AgentProviderRegistry,
    get_provider_registry,
)
from app.services.containers import ContainerService, get_container_service
from app.services.conversation_service import (
    ConversationService,
    SearchResult,
    get_conversation_service,
)
from app.services.usage_recorder import UsageEntry, UsageRecorder
from app.utils.tools.location import build_web_search_location

logger = logging.getLogger(__name__)


class AgentService:
    """Core façade that orchestrates agent interactions."""

    def __init__(
        self,
        *,
        conversation_repo: ConversationRepository | None = None,
        conversation_service: ConversationService | None = None,
        usage_recorder: UsageRecorder | None = None,
        provider_registry: AgentProviderRegistry | None = None,
        container_service: ContainerService | None = None,
    ) -> None:
        self._conversation_service = conversation_service or get_conversation_service()
        if conversation_repo is not None:
            self._conversation_service.set_repository(conversation_repo)

        self._usage_recorder = usage_recorder
        self._provider_registry = provider_registry or get_provider_registry()
        self._container_service = container_service or get_container_service()

    async def chat(
        self, request: AgentChatRequest, *, actor: ConversationActorContext
    ) -> AgentChatResponse:
        provider = self._get_provider()
        descriptor = provider.resolve_agent(request.agent_type)
        conversation_id = request.conversation_id or str(uuid.uuid4())
        container_bindings = await self._resolve_container_bindings_for_tenant(
            tenant_id=actor.tenant_id
        )
        runtime_ctx = PromptRuntimeContext(
            actor=actor,
            conversation_id=conversation_id,
            request_message=request.message,
            settings=get_settings(),
            user_location=build_web_search_location(
                request.location, share_location=request.share_location
            ),
            container_bindings=container_bindings,
        )
        state = await self._conversation_service.get_session_state(
            conversation_id, tenant_id=actor.tenant_id
        )
        provider_conversation_id = await self._resolve_provider_conversation_id(
            provider=provider,
            actor=actor,
            conversation_id=conversation_id,
            existing_state=state,
        )
        session_id, session_handle = await self._acquire_session(
            provider, actor.tenant_id, conversation_id, provider_conversation_id
        )

        user_message = ConversationMessage(role="user", content=request.message)
        await self._conversation_service.append_message(
            conversation_id,
            user_message,
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
            run_options = self._build_run_options(request.run_options)
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

        assistant_message = ConversationMessage(
            role="assistant",
            content=str(result.final_output),
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
            actor.tenant_id,
            conversation_id,
            session_id,
            provider_name=provider.name,
            provider_conversation_id=provider_conversation_id,
        )
        await self._record_usage_metrics(
            tenant_id=actor.tenant_id,
            conversation_id=conversation_id,
            response_id=result.response_id,
            usage=result.usage,
        )

        tool_overview = provider.tool_overview()
        return AgentChatResponse(
            response=str(result.final_output),
            conversation_id=conversation_id,
            agent_used=descriptor.key,
            handoff_occurred=False,
            metadata={
                "model_used": descriptor.model,
                "tools_available": tool_overview.get("tool_names", []),
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
        container_bindings = await self._resolve_container_bindings_for_tenant(
            tenant_id=actor.tenant_id
        )
        runtime_ctx = PromptRuntimeContext(
            actor=actor,
            conversation_id=conversation_id,
            request_message=request.message,
            settings=get_settings(),
            user_location=build_web_search_location(
                request.location, share_location=request.share_location
            ),
            container_bindings=container_bindings,
        )
        state = await self._conversation_service.get_session_state(
            conversation_id, tenant_id=actor.tenant_id
        )
        provider_conversation_id = await self._resolve_provider_conversation_id(
            provider=provider,
            actor=actor,
            conversation_id=conversation_id,
            existing_state=state,
        )
        session_id, session_handle = await self._acquire_session(
            provider, actor.tenant_id, conversation_id, provider_conversation_id
        )

        user_message = ConversationMessage(role="user", content=request.message)
        await self._conversation_service.append_message(
            conversation_id,
            user_message,
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

        complete_response = ""
        token = set_current_actor(actor)
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
            allow_openai_uuid_fallback = os.getenv(
                "ALLOW_OPENAI_CONVERSATION_UUID_FALLBACK", ""
            ).lower() in ("1", "true", "yes")
            if runtime_conversation_id is None:
                if provider.name != "openai":
                    runtime_conversation_id = conversation_id
                elif allow_openai_uuid_fallback:
                    runtime_conversation_id = conversation_id
            lifecycle_bus = LifecycleEventBus()
            run_options = self._build_run_options(request.run_options, hook_sink=lifecycle_bus)
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

                    yield event

                    if event.is_terminal:
                        break
                # Drain any remaining lifecycle events
                async for leftover in lifecycle_bus.drain():
                    leftover.conversation_id = conversation_id
                    yield leftover
        finally:
            reset_current_actor(token)

        assistant_message = ConversationMessage(
            role="assistant",
            content=complete_response,
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
                "response_id": stream_handle.last_response_id,
            },
        )
        await self._sync_session_state(
            actor.tenant_id,
            conversation_id,
            session_id,
            provider_name=provider.name,
            provider_conversation_id=provider_conversation_id,
        )
        await self._record_usage_metrics(
            tenant_id=actor.tenant_id,
            conversation_id=conversation_id,
            response_id=stream_handle.last_response_id,
            usage=stream_handle.usage,
        )

    async def get_conversation_history(
        self, conversation_id: str, *, actor: ConversationActorContext
    ) -> ConversationHistory:
        messages = await self._conversation_service.get_messages(
            conversation_id, tenant_id=actor.tenant_id
        )
        if not messages:
            raise ValueError(f"Conversation {conversation_id} not found")

        api_messages = [self._to_chat_message(msg) for msg in messages]
        return ConversationHistory(
            conversation_id=conversation_id,
            messages=api_messages,
            created_at=messages[0].timestamp.isoformat(),
            updated_at=messages[-1].timestamp.isoformat(),
        )

    async def list_conversations(
        self,
        *,
        actor: ConversationActorContext,
        limit: int = 50,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
        updated_after: datetime | None = None,
    ) -> tuple[list[ConversationSummary], str | None]:
        page = await self._conversation_service.paginate_conversations(
            tenant_id=actor.tenant_id,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent_entrypoint,
            updated_after=updated_after,
        )

        summaries: list[ConversationSummary] = []
        for record in page.items:
            if not record.messages:
                continue
            last_message = record.messages[-1]
            summaries.append(
                ConversationSummary(
                    conversation_id=record.conversation_id,
                    message_count=len(record.messages),
                    last_message=last_message.content[:160],
                    created_at=record.created_at.isoformat(),
                    updated_at=record.updated_at.isoformat(),
                )
            )

        return summaries, page.next_cursor

    async def search_conversations(
        self,
        *,
        actor: ConversationActorContext,
        query: str,
        limit: int = 20,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
    ) -> tuple[list[SearchResult], str | None]:
        page = await self._conversation_service.search(
            tenant_id=actor.tenant_id,
            query=query,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent_entrypoint,
        )
        return page.items, page.next_cursor

    async def clear_conversation(
        self,
        conversation_id: str,
        *,
        actor: ConversationActorContext,
    ) -> None:
        await self._conversation_service.clear_conversation(
            conversation_id, tenant_id=actor.tenant_id
        )

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

    async def _resolve_container_bindings_for_tenant(
        self, *, tenant_id: str
    ) -> dict[str, str] | None:
        if not self._container_service:
            return None
        try:
            bindings = await self._container_service.list_agent_bindings(
                tenant_id=uuid.UUID(tenant_id)
            )
        except Exception:
            return None
        return bindings or None

    def _get_provider(self):
        try:
            return self._provider_registry.get_default()
        except RuntimeError as exc:
            raise RuntimeError(
                "No agent providers registered. Register a provider (e.g., build_openai_provider)"
                " before invoking AgentService, or use the test fixture that populates the"
                " AgentProviderRegistry."
            ) from exc

    async def _acquire_session(
        self,
        provider,
        tenant_id: str,
        conversation_id: str,
        provider_conversation_id: str | None,
    ) -> tuple[str, Any]:
        state = await self._conversation_service.get_session_state(
            conversation_id, tenant_id=tenant_id
        )
        rebind_to_provider = os.getenv("FORCE_PROVIDER_SESSION_REBIND", "").lower() in (
            "1",
            "true",
            "yes",
        )
        if provider_conversation_id and (
            rebind_to_provider or not (state and state.sdk_session_id)
        ):
            session_id = provider_conversation_id
        elif state and state.sdk_session_id:
            session_id = state.sdk_session_id
        else:
            session_id = conversation_id
        session_handle = provider.session_store.build(session_id)
        return session_id, session_handle

    async def _sync_session_state(
        self,
        tenant_id: str,
        conversation_id: str,
        session_id: str,
        *,
        provider_name: str | None,
        provider_conversation_id: str | None,
    ) -> None:
        await self._conversation_service.update_session_state(
            conversation_id,
            tenant_id=tenant_id,
            state=ConversationSessionState(
                provider=provider_name,
                provider_conversation_id=provider_conversation_id,
                sdk_session_id=session_id,
                last_session_sync_at=datetime.now(UTC),
            ),
        )

    async def _record_usage_metrics(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        response_id: str | None,
        usage: AgentRunUsage | None,
    ) -> None:
        if not self._usage_recorder:
            return
        timestamp = datetime.now(UTC)
        base_key = response_id or f"{conversation_id}:{uuid.uuid4()}"
        entries: list[UsageEntry] = [
            UsageEntry(
                feature_key="messages",
                quantity=1,
                idempotency_key=f"{base_key}:messages",
                period_start=timestamp,
                period_end=timestamp,
            )
        ]

        if usage:
            if usage.input_tokens:
                entries.append(
                    UsageEntry(
                        feature_key="input_tokens",
                        quantity=int(usage.input_tokens),
                        idempotency_key=f"{base_key}:input_tokens",
                        period_start=timestamp,
                        period_end=timestamp,
                    )
                )
            if usage.output_tokens:
                entries.append(
                    UsageEntry(
                        feature_key="output_tokens",
                        quantity=int(usage.output_tokens),
                        idempotency_key=f"{base_key}:output_tokens",
                        period_start=timestamp,
                        period_end=timestamp,
                    )
                )

        await self._usage_recorder.record_batch(tenant_id, entries)

    @staticmethod
    def _build_run_options(payload: Any, hook_sink: Any | None = None) -> RunOptions | None:
        if not payload:
            return RunOptions(hook_sink=hook_sink) if hook_sink else None
        return RunOptions(
            max_turns=getattr(payload, "max_turns", None),
            previous_response_id=getattr(payload, "previous_response_id", None),
            handoff_input_filter=getattr(payload, "handoff_input_filter", None),
            run_config=getattr(payload, "run_config", None),
            hook_sink=hook_sink,
        )

    @staticmethod
    def _to_chat_message(message: ConversationMessage) -> ChatMessage:
        return ChatMessage(
            role=message.role,
            content=message.content,
            timestamp=message.timestamp.isoformat(),
        )

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

    async def _resolve_provider_conversation_id(
        self,
        *,
        provider,
        actor: ConversationActorContext,
        conversation_id: str,
        existing_state: ConversationSessionState | None,
    ) -> str | None:
        if existing_state and existing_state.provider_conversation_id:
            if existing_state.provider_conversation_id.startswith("conv_"):
                return existing_state.provider_conversation_id
            logger.warning(
                "Ignoring non-conv provider conversation id for conversation %s: %s",
                conversation_id,
                existing_state.provider_conversation_id,
            )
        if os.getenv("DISABLE_PROVIDER_CONVERSATION_CREATION", "").lower() in (
            "1",
            "true",
            "yes",
        ):
            return None

        factory = getattr(provider, "conversation_factory", None)
        if not factory:
            return None

        try:
            candidate = await factory.create(
                tenant_id=actor.tenant_id,
                user_id=actor.user_id,
                conversation_key=conversation_id,
            )
            if not (candidate or "").startswith("conv_"):
                logger.warning(
                    "Provider conversation id did not match expected format; ignoring: %s",
                    candidate,
                )
                return None
            return candidate
        except Exception:  # pragma: no cover - defensive fallback
            logger.exception("Failed to create provider conversation; proceeding without conv id.")
            return None


def build_agent_service(
    *,
    conversation_service: ConversationService | None = None,
    conversation_repository: ConversationRepository | None = None,
    usage_recorder: UsageRecorder | None = None,
    provider_registry: AgentProviderRegistry | None = None,
) -> AgentService:
    return AgentService(
        conversation_repo=conversation_repository,
        conversation_service=conversation_service,
        usage_recorder=usage_recorder,
        provider_registry=provider_registry,
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
