"""Core agent orchestration services."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from agents import trace

from app.api.v1.agents.schemas import AgentStatus, AgentSummary
from app.api.v1.chat.schemas import AgentChatRequest, AgentChatResponse, StreamingChatResponse
from app.api.v1.conversations.schemas import ChatMessage, ConversationHistory, ConversationSummary
from app.domain.ai import AgentRunUsage
from app.domain.conversations import (
    ConversationMessage,
    ConversationMetadata,
    ConversationRepository,
    ConversationSessionState,
)
from app.services.agents.context import (
    ConversationActorContext,
    reset_current_actor,
    set_current_actor,
)
from app.services.agents.provider_registry import (
    AgentProviderRegistry,
    get_provider_registry,
)
from app.services.conversation_service import ConversationService, get_conversation_service
from app.services.usage_recorder import UsageEntry, UsageRecorder


class AgentService:
    """Core façade that orchestrates agent interactions."""

    def __init__(
        self,
        *,
        conversation_repo: ConversationRepository | None = None,
        conversation_service: ConversationService | None = None,
        usage_recorder: UsageRecorder | None = None,
        provider_registry: AgentProviderRegistry | None = None,
    ) -> None:
        self._conversation_service = conversation_service or get_conversation_service()
        if conversation_repo is not None:
            self._conversation_service.set_repository(conversation_repo)

        self._usage_recorder = usage_recorder
        self._provider_registry = provider_registry or get_provider_registry()

    async def chat(
        self, request: AgentChatRequest, *, actor: ConversationActorContext
    ) -> AgentChatResponse:
        provider = self._get_provider()
        descriptor = provider.resolve_agent(request.agent_type)
        conversation_id = request.conversation_id or str(uuid.uuid4())
        session_id, session_handle = await self._acquire_session(
            provider, actor.tenant_id, conversation_id
        )

        user_message = ConversationMessage(role="user", content=request.message)
        await self._conversation_service.append_message(
            conversation_id,
            user_message,
            tenant_id=actor.tenant_id,
            metadata=self._build_metadata(
                tenant_id=actor.tenant_id,
                agent_entrypoint=request.agent_type or descriptor.key,
                active_agent=descriptor.key,
                session_id=session_id,
                user_id=actor.user_id,
            ),
        )

        token = set_current_actor(actor)
        try:
            with trace(workflow_name="Agent Chat", group_id=conversation_id):
                result = await provider.runtime.run(
                    descriptor.key,
                    request.message,
                    session=session_handle,
                    conversation_id=conversation_id,
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
                agent_entrypoint=request.agent_type or descriptor.key,
                active_agent=descriptor.key,
                session_id=session_id,
                user_id=actor.user_id,
            ),
        )
        await self._sync_session_state(actor.tenant_id, conversation_id, session_id)
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
    ) -> AsyncGenerator[StreamingChatResponse, None]:
        provider = self._get_provider()
        descriptor = provider.resolve_agent(request.agent_type)
        conversation_id = request.conversation_id or str(uuid.uuid4())
        session_id, session_handle = await self._acquire_session(
            provider, actor.tenant_id, conversation_id
        )

        user_message = ConversationMessage(role="user", content=request.message)
        await self._conversation_service.append_message(
            conversation_id,
            user_message,
            tenant_id=actor.tenant_id,
            metadata=self._build_metadata(
                tenant_id=actor.tenant_id,
                agent_entrypoint=request.agent_type or descriptor.key,
                active_agent=descriptor.key,
                session_id=session_id,
                user_id=actor.user_id,
            ),
        )

        complete_response = ""
        token = set_current_actor(actor)
        try:
            with trace(workflow_name="Agent Chat Stream", group_id=conversation_id):
                stream_handle = provider.runtime.run_stream(
                    descriptor.key,
                    request.message,
                    session=session_handle,
                    conversation_id=conversation_id,
                )
                async for event in stream_handle.events():
                    if event.content_delta:
                        complete_response += event.content_delta
                        yield StreamingChatResponse(
                            chunk=event.content_delta,
                            conversation_id=conversation_id,
                            is_complete=False,
                            agent_used=descriptor.key,
                        )
                    if event.is_terminal:
                        yield StreamingChatResponse(
                            chunk="",
                            conversation_id=conversation_id,
                            is_complete=True,
                            agent_used=descriptor.key,
                        )
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
                agent_entrypoint=request.agent_type or descriptor.key,
                active_agent=descriptor.key,
                session_id=session_id,
                user_id=actor.user_id,
            ),
        )
        await self._sync_session_state(actor.tenant_id, conversation_id, session_id)
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
    ) -> list[ConversationSummary]:
        summaries: list[ConversationSummary] = []

        for record in await self._conversation_service.iterate_conversations(
            tenant_id=actor.tenant_id
        ):
            if not record.messages:
                continue

            last_message = record.messages[-1]
            summaries.append(
                ConversationSummary(
                    conversation_id=record.conversation_id,
                    message_count=len(record.messages),
                    last_message=last_message.content[:120],
                    created_at=record.created_at.isoformat(),
                    updated_at=record.updated_at.isoformat(),
                )
            )

        summaries.sort(key=lambda item: item.updated_at, reverse=True)
        return summaries

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
        self, provider, tenant_id: str, conversation_id: str
    ) -> tuple[str, Any]:
        state = await self._conversation_service.get_session_state(
            conversation_id, tenant_id=tenant_id
        )
        if state and state.sdk_session_id:
            session_id = state.sdk_session_id
        else:
            session_id = conversation_id
        session_handle = provider.session_store.build(session_id)
        return session_id, session_handle

    async def _sync_session_state(
        self, tenant_id: str, conversation_id: str, session_id: str
    ) -> None:
        await self._conversation_service.update_session_state(
            conversation_id,
            tenant_id=tenant_id,
            state=ConversationSessionState(
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
        agent_entrypoint: str,
        active_agent: str,
        session_id: str,
        user_id: str,
    ) -> ConversationMetadata:
        return ConversationMetadata(
            tenant_id=tenant_id,
            agent_entrypoint=agent_entrypoint,
            active_agent=active_agent,
            sdk_session_id=session_id,
            user_id=user_id,
        )


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
