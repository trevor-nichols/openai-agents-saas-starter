"""Conversation orchestration utilities sitting atop the repository layer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.domain.conversations import (
    ConversationMessage,
    ConversationMetadata,
    ConversationRecord,
    ConversationRepository,
    ConversationSessionState,
)


@dataclass(slots=True)
class SearchResult:
    conversation_id: str
    preview: str


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

    async def clear_conversation(self, conversation_id: str, *, tenant_id: str) -> None:
        normalized_tenant = _require_tenant_id(tenant_id)
        await self._require_repository().clear_conversation(
            conversation_id, tenant_id=normalized_tenant
        )

    async def search(self, *, tenant_id: str, query: str) -> list[SearchResult]:
        """Lightweight search for conversation previews matching the query."""

        normalized = query.lower()
        matches: list[SearchResult] = []

        normalized_tenant = _require_tenant_id(tenant_id)
        for record in await self._require_repository().iter_conversations(
            tenant_id=normalized_tenant
        ):
            for message in record.messages:
                if normalized in message.content.lower():
                    preview = message.content[:120]
                    suffix = "..." if len(message.content) > 120 else ""
                    matches.append(
                        SearchResult(
                            conversation_id=record.conversation_id,
                            preview=f"{preview}{suffix}",
                        )
                    )
                    break

        return matches

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
