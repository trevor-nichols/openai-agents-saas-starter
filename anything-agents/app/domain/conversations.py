"""Domain models and contracts for conversation data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol


@dataclass(slots=True)
class ConversationMessage:
    """Domain representation of a single conversational message."""

    role: Literal["user", "assistant", "system"]
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


@dataclass(slots=True)
class ConversationMetadata:
    """Optional metadata captured alongside a conversation event."""

    agent_entrypoint: str
    active_agent: str | None = None
    source_channel: str | None = None
    topic_hint: str | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    handoff_count: int | None = None
    total_tokens_prompt: int | None = None
    total_tokens_completion: int | None = None
    reasoning_tokens: int | None = None
    sdk_session_id: str | None = None
    session_cursor: str | None = None
    last_session_sync_at: datetime | None = None


@dataclass(slots=True)
class ConversationSessionState:
    """State container describing the SDK session associated with a conversation."""

    sdk_session_id: str | None = None
    session_cursor: str | None = None
    last_session_sync_at: datetime | None = None


class ConversationRepository(Protocol):
    """Persistence contract for storing conversation histories."""

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
        *,
        metadata: ConversationMetadata,
    ) -> None: ...

    async def get_messages(self, conversation_id: str) -> list[ConversationMessage]: ...

    async def list_conversation_ids(self) -> list[str]: ...

    async def iter_conversations(self) -> list[ConversationRecord]: ...

    async def clear_conversation(self, conversation_id: str) -> None: ...

    async def get_session_state(self, conversation_id: str) -> ConversationSessionState | None: ...

    async def upsert_session_state(
        self, conversation_id: str, state: ConversationSessionState
    ) -> None: ...
