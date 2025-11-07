"""Conversation orchestration utilities sitting atop the repository layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.domain.conversations import (
    ConversationMetadata,
    ConversationMessage,
    ConversationRecord,
    ConversationRepository,
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
        metadata: ConversationMetadata,
    ) -> None:
        repository = self._require_repository()
        await repository.add_message(
            conversation_id,
            message,
            metadata=metadata,
        )

    async def get_messages(self, conversation_id: str) -> list[ConversationMessage]:
        return await self._require_repository().get_messages(conversation_id)

    async def list_conversation_ids(self) -> list[str]:
        return await self._require_repository().list_conversation_ids()

    async def iterate_conversations(self) -> Iterable[ConversationRecord]:
        return await self._require_repository().iter_conversations()

    async def clear_conversation(self, conversation_id: str) -> None:
        await self._require_repository().clear_conversation(conversation_id)

    async def search(self, query: str) -> list[SearchResult]:
        """Lightweight search for conversation previews matching the query."""

        normalized = query.lower()
        matches: list[SearchResult] = []

        for record in await self._require_repository().iter_conversations():
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


conversation_service = ConversationService()
