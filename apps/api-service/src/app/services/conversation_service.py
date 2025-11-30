"""Conversation orchestration utilities sitting atop the repository layer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from app.domain.conversations import (
    ConversationEvent,
    ConversationMessage,
    ConversationMetadata,
    ConversationPage,
    ConversationRecord,
    ConversationRepository,
    ConversationSessionState,
)


@dataclass(slots=True)
class SearchResult:
    conversation_id: str
    preview: str
    score: float | None = None
    updated_at: datetime | None = None


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
    ) -> None:
        repository = self._require_repository()
        normalized_tenant = _require_tenant_id(tenant_id)
        _ensure_metadata_tenant(metadata, normalized_tenant)
        await repository.add_message(
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

    async def clear_conversation(self, conversation_id: str, *, tenant_id: str) -> None:
        normalized_tenant = _require_tenant_id(tenant_id)
        await self._require_repository().clear_conversation(
            conversation_id, tenant_id=normalized_tenant
        )

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
                    preview=preview,
                    score=hit.score,
                    updated_at=hit.record.updated_at,
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


def _ensure_metadata_tenant(metadata: ConversationMetadata, tenant_id: str) -> None:
    if metadata.tenant_id != tenant_id:
        raise ValueError("ConversationMetadata tenant_id mismatch")


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
