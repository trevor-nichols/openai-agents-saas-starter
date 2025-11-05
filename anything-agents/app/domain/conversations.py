"""Domain models and contracts for conversation data."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class ConversationMessage:
    """Domain representation of a single conversational message."""

    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class ConversationRecord:
    """Aggregate containing an identifier and its message history."""

    conversation_id: str
    messages: list[ConversationMessage]

    @property
    def created_at(self) -> datetime:
        return self.messages[0].timestamp if self.messages else datetime.utcnow()

    @property
    def updated_at(self) -> datetime:
        return self.messages[-1].timestamp if self.messages else datetime.utcnow()


class ConversationRepository(Protocol):
    """Persistence contract for storing conversation histories."""

    def add_message(self, conversation_id: str, message: ConversationMessage) -> None:
        ...

    def get_messages(self, conversation_id: str) -> list[ConversationMessage]:
        ...

    def list_conversation_ids(self) -> list[str]:
        ...

    def iter_conversations(self) -> Iterable[ConversationRecord]:
        ...

    def clear_conversation(self, conversation_id: str) -> None:
        ...
