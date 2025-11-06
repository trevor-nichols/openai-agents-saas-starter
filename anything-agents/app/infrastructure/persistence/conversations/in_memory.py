"""In-memory conversation repository implementation."""

from __future__ import annotations

from collections.abc import Iterable
from threading import RLock

from app.domain.conversations import (
    ConversationMetadata,
    ConversationMessage,
    ConversationRecord,
    ConversationRepository,
)


class InMemoryConversationRepository(ConversationRepository):
    """Thread-safe in-memory store for conversation history."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._store: dict[str, list[ConversationMessage]] = {}
        self._metadata: dict[str, ConversationMetadata] = {}

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
        *,
        metadata: ConversationMetadata,
    ) -> None:
        with self._lock:
            history = self._store.setdefault(conversation_id, [])
            history.append(message)
            self._metadata[conversation_id] = metadata

    async def get_messages(self, conversation_id: str) -> list[ConversationMessage]:
        with self._lock:
            return list(self._store.get(conversation_id, []))

    async def list_conversation_ids(self) -> list[str]:
        with self._lock:
            return list(self._store.keys())

    async def iter_conversations(self) -> list[ConversationRecord]:
        with self._lock:
            return [
                ConversationRecord(conversation_id=conversation_id, messages=list(messages))
                for conversation_id, messages in self._store.items()
            ]

    async def clear_conversation(self, conversation_id: str) -> None:
        with self._lock:
            self._store.pop(conversation_id, None)
            self._metadata.pop(conversation_id, None)
