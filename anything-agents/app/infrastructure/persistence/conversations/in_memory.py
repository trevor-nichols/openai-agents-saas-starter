"""In-memory conversation repository implementation."""

from __future__ import annotations

from collections.abc import Iterable
from threading import RLock

from app.domain.conversations import ConversationMessage, ConversationRecord, ConversationRepository


class InMemoryConversationRepository(ConversationRepository):
    """Thread-safe in-memory store for conversation history."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._store: dict[str, list[ConversationMessage]] = {}

    def add_message(self, conversation_id: str, message: ConversationMessage) -> None:
        with self._lock:
            history = self._store.setdefault(conversation_id, [])
            history.append(message)

    def get_messages(self, conversation_id: str) -> list[ConversationMessage]:
        with self._lock:
            return list(self._store.get(conversation_id, []))

    def list_conversation_ids(self) -> list[str]:
        with self._lock:
            return list(self._store.keys())

    def iter_conversations(self) -> Iterable[ConversationRecord]:
        with self._lock:
            for conversation_id, messages in self._store.items():
                yield ConversationRecord(
                    conversation_id=conversation_id,
                    messages=list(messages),
                )

    def clear_conversation(self, conversation_id: str) -> None:
        with self._lock:
            self._store.pop(conversation_id, None)
