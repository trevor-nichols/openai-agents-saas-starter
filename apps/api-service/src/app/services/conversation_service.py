"""Conversation orchestration utilities sitting atop the repository layer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.domain.conversation_titles import normalize_display_name
from app.domain.conversations import (
    ConversationEvent,
    ConversationMemoryConfig,
    ConversationMessage,
    ConversationMetadata,
    ConversationPage,
    ConversationRecord,
    ConversationRepository,
    ConversationRunUsage,
    ConversationSessionState,
    MessagePage,
    ensure_metadata_tenant,
)
from app.services.activity import activity_service


@dataclass(slots=True)
class SearchResult:
    conversation_id: str
    preview: str
    score: float | None = None
    updated_at: datetime | None = None
    display_name: str | None = None
    agent_entrypoint: str | None = None
    active_agent: str | None = None
    topic_hint: str | None = None
    status: str | None = None
    last_message_preview: str | None = None


@dataclass(slots=True)
class SearchPage:
    items: list[SearchResult]
    next_cursor: str | None


class ConversationService:
    """High-level façade that coordinates conversation persistence concerns."""

    def __init__(self, repository: ConversationRepository | None = None) -> None:
        self._repository: ConversationRepository | None = repository

    def set_repository(self, repository: ConversationRepository) -> None:
        """Swap the underlying conversation store."""

        self._repository = repository

    async def conversation_exists(self, conversation_id: str, *, tenant_id: str) -> bool:
        """Return True when a conversation already exists for the tenant."""

        normalized_tenant = _require_tenant_id(tenant_id)
        state = await self._require_repository().get_session_state(
            conversation_id, tenant_id=normalized_tenant
        )
        return state is not None

    async def record_conversation_created(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        agent_entrypoint: str | None = None,
        existed: bool | None = None,
    ) -> None:
        """Best-effort activity hook when a new conversation is started."""

        normalized_tenant = _require_tenant_id(tenant_id)
        already_exists = existed if existed is not None else await self.conversation_exists(
            conversation_id, tenant_id=normalized_tenant
        )
        if already_exists:
            return

        try:
            metadata = {"conversation_id": conversation_id}
            if agent_entrypoint:
                metadata["agent_entrypoint"] = agent_entrypoint
            await activity_service.record(
                tenant_id=normalized_tenant,
                action="conversation.created",
                object_type="conversation",
                object_id=conversation_id,
                source="api",
                metadata=metadata,
            )
        except Exception:  # pragma: no cover - best effort
            pass

    @property
    def repository(self) -> ConversationRepository:
        return self._require_repository()

    def _require_repository(self) -> ConversationRepository:
        if self._repository is None:
            raise RuntimeError("Conversation repository has not been configured yet.")
        return self._repository

    async def append_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
        *,
        tenant_id: str,
        metadata: ConversationMetadata,
    ) -> int | None:
        repository = self._require_repository()
        normalized_tenant = _require_tenant_id(tenant_id)
        ensure_metadata_tenant(metadata, normalized_tenant)
        return await repository.add_message(
            conversation_id,
            message,
            tenant_id=normalized_tenant,
            metadata=metadata,
        )

    async def get_messages(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
    ) -> list[ConversationMessage]:
        normalized_tenant = _require_tenant_id(tenant_id)
        return await self._require_repository().get_messages(
            conversation_id, tenant_id=normalized_tenant
        )

    async def get_conversation(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
    ) -> ConversationRecord | None:
        normalized_tenant = _require_tenant_id(tenant_id)
        return await self._require_repository().get_conversation(
            conversation_id, tenant_id=normalized_tenant
        )

    async def list_conversation_ids(self, *, tenant_id: str) -> list[str]:
        normalized_tenant = _require_tenant_id(tenant_id)
        return await self._require_repository().list_conversation_ids(
            tenant_id=normalized_tenant
        )

    async def iterate_conversations(
        self,
        *,
        tenant_id: str,
    ) -> Iterable[ConversationRecord]:
        normalized_tenant = _require_tenant_id(tenant_id)
        return await self._require_repository().iter_conversations(tenant_id=normalized_tenant)

    async def paginate_conversations(
        self,
        *,
        tenant_id: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
        updated_after: datetime | None = None,
    ) -> ConversationPage:
        normalized_tenant = _require_tenant_id(tenant_id)
        return await self._require_repository().paginate_conversations(
            tenant_id=normalized_tenant,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent_entrypoint,
            updated_after=updated_after,
        )

    async def paginate_messages(
        self,
        *,
        conversation_id: str,
        tenant_id: str,
        limit: int,
        cursor: str | None = None,
        direction: Literal["asc", "desc"] = "desc",
    ) -> MessagePage:
        normalized_tenant = _require_tenant_id(tenant_id)
        direction_normalized: Literal["asc", "desc"] = (
            "asc" if (direction or "desc").lower() == "asc" else "desc"
        )
        return await self._require_repository().paginate_messages(
            conversation_id=conversation_id,
            tenant_id=normalized_tenant,
            limit=limit,
            cursor=cursor,
            direction=direction_normalized,
        )

    async def clear_conversation(self, conversation_id: str, *, tenant_id: str) -> None:
        normalized_tenant = _require_tenant_id(tenant_id)
        await self._require_repository().clear_conversation(
            conversation_id, tenant_id=normalized_tenant
        )
        try:
            await activity_service.record(
                tenant_id=normalized_tenant,
                action="conversation.cleared",
                object_type="conversation",
                object_id=conversation_id,
                source="api",
                metadata={"conversation_id": conversation_id},
            )
        except Exception:  # pragma: no cover - best effort
            pass

    async def search(
        self,
        *,
        tenant_id: str,
        query: str,
        limit: int = 20,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
    ) -> SearchPage:
        normalized_query = (query or "").strip()
        if not normalized_query:
            return SearchPage(items=[], next_cursor=None)

        normalized_tenant = _require_tenant_id(tenant_id)
        page = await self._require_repository().search_conversations(
            tenant_id=normalized_tenant,
            query=normalized_query,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent_entrypoint,
        )

        items: list[SearchResult] = []
        for hit in page.items:
            preview = _build_preview(hit.record.messages, normalized_query)
            items.append(
                SearchResult(
                    conversation_id=hit.record.conversation_id,
                    display_name=hit.record.display_name,
                    preview=preview,
                    score=hit.score,
                    updated_at=hit.record.updated_at,
                    agent_entrypoint=hit.record.agent_entrypoint,
                    active_agent=hit.record.active_agent,
                    topic_hint=hit.record.topic_hint,
                    status=hit.record.status,
                    last_message_preview=hit.record.messages[-1].content[:160]
                    if hit.record.messages
                    else None,
                )
            )

        return SearchPage(items=items, next_cursor=page.next_cursor)

    async def get_session_state(
        self, conversation_id: str, *, tenant_id: str
    ) -> ConversationSessionState | None:
        normalized_tenant = _require_tenant_id(tenant_id)
        return await self._require_repository().get_session_state(
            conversation_id, tenant_id=normalized_tenant
        )

    async def get_memory_config(
        self, conversation_id: str, *, tenant_id: str
    ) -> ConversationMemoryConfig | None:
        normalized_tenant = _require_tenant_id(tenant_id)
        return await self._require_repository().get_memory_config(
            conversation_id, tenant_id=normalized_tenant
        )

    async def set_memory_config(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        config: ConversationMemoryConfig,
        provided_fields: set[str] | None = None,
    ) -> None:
        normalized_tenant = _require_tenant_id(tenant_id)
        await self._require_repository().set_memory_config(
            conversation_id,
            tenant_id=normalized_tenant,
            config=config,
            provided_fields=provided_fields,
        )

    async def persist_summary(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        agent_key: str | None,
        summary_text: str,
        summary_model: str | None = None,
        summary_length_tokens: int | None = None,
        version: str | None = None,
    ) -> None:
        normalized_tenant = _require_tenant_id(tenant_id)
        await self._require_repository().persist_summary(
            conversation_id,
            tenant_id=normalized_tenant,
            agent_key=agent_key,
            summary_text=summary_text,
            summary_model=summary_model,
            summary_length_tokens=summary_length_tokens,
            version=version,
        )

    async def get_latest_summary(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        agent_key: str | None,
        max_age_seconds: int | None = None,
    ):
        normalized_tenant = _require_tenant_id(tenant_id)
        return await self._require_repository().get_latest_summary(
            conversation_id,
            tenant_id=normalized_tenant,
            agent_key=agent_key,
            max_age_seconds=max_age_seconds,
        )

    async def persist_run_usage(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        usage: ConversationRunUsage,
    ) -> None:
        normalized_tenant = _require_tenant_id(tenant_id)
        await self._require_repository().add_run_usage(
            conversation_id, tenant_id=normalized_tenant, usage=usage
        )

    async def list_run_usage(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        limit: int = 20,
    ) -> list[ConversationRunUsage]:
        normalized_tenant = _require_tenant_id(tenant_id)
        return await self._require_repository().list_run_usage(
            conversation_id, tenant_id=normalized_tenant, limit=limit
        )

    async def update_session_state(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        state: ConversationSessionState,
    ) -> None:
        normalized_tenant = _require_tenant_id(tenant_id)
        await self._require_repository().upsert_session_state(
            conversation_id,
            tenant_id=normalized_tenant,
            state=state,
        )

    async def append_run_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        events: list[ConversationEvent],
    ) -> None:
        if not events:
            return
        normalized_tenant = _require_tenant_id(tenant_id)
        await self._require_repository().add_run_events(
            conversation_id,
            tenant_id=normalized_tenant,
            events=events,
        )

    async def get_run_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        workflow_run_id: str | None = None,
    ) -> list[ConversationEvent]:
        normalized_tenant = _require_tenant_id(tenant_id)
        return await self._require_repository().get_run_events(
            conversation_id,
            tenant_id=normalized_tenant,
            workflow_run_id=workflow_run_id,
        )

    async def set_display_name(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        display_name: str,
        generated_at: datetime | None = None,
    ) -> bool:
        normalized_tenant = _require_tenant_id(tenant_id)
        return await self._require_repository().set_display_name(
            conversation_id,
            tenant_id=normalized_tenant,
            display_name=display_name,
            generated_at=generated_at,
        )

    async def update_display_name(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        display_name: str,
    ) -> str:
        normalized_tenant = _require_tenant_id(tenant_id)
        normalized_title = normalize_display_name(display_name)
        await self._require_repository().update_display_name(
            conversation_id,
            tenant_id=normalized_tenant,
            display_name=normalized_title,
        )

        try:
            await activity_service.record(
                tenant_id=normalized_tenant,
                action="conversation.title.updated",
                object_type="conversation",
                object_id=conversation_id,
                source="api",
                metadata={
                    "conversation_id": conversation_id,
                    "display_name_length": len(normalized_title),
                },
            )
        except Exception:  # pragma: no cover - best effort
            pass
        return normalized_title


def get_conversation_service() -> ConversationService:
    """Resolve the container-backed conversation service."""

    from app.bootstrap.container import get_container

    return get_container().conversation_service


class _ConversationServiceHandle:
    """Proxy exposing the active conversation service instance."""

    def __getattr__(self, name: str):
        return getattr(get_conversation_service(), name)


conversation_service = _ConversationServiceHandle()


def _require_tenant_id(value: str) -> str:
    tenant = (value or "").strip()
    if not tenant:
        raise ValueError("tenant_id is required for conversation operations")
    return tenant


def _build_preview(messages: list[ConversationMessage], query: str) -> str:
    if not messages:
        return ""
    normalized = query.lower()
    for message in messages:
        if normalized in message.content.lower():
            text = message.content
            break
    else:
        text = messages[-1].content

    preview = text[:160]
    return f"{preview}..." if len(text) > 160 else preview
