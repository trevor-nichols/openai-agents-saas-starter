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
class ConversationPage:
    """Page of conversations plus a cursor for keyset pagination."""

    items: list[ConversationRecord]
    next_cursor: str | None


@dataclass(slots=True)
class ConversationSearchHit:
    """Search hit with relevance score."""

    record: ConversationRecord
    score: float


@dataclass(slots=True)
class ConversationSearchPage:
    """Page of search hits with pagination cursor."""

    items: list[ConversationSearchHit]
    next_cursor: str | None


@dataclass(slots=True)
class ConversationMetadata:
    """Metadata captured alongside a conversation event."""

    tenant_id: str
    agent_entrypoint: str
    provider: str | None = None
    provider_conversation_id: str | None = None
    active_agent: str | None = None
    source_channel: str | None = None
    topic_hint: str | None = None
    user_id: str | None = None
    handoff_count: int | None = None
    total_tokens_prompt: int | None = None
    total_tokens_completion: int | None = None
    reasoning_tokens: int | None = None
    sdk_session_id: str | None = None
    session_cursor: str | None = None
    last_session_sync_at: datetime | None = None

    def __post_init__(self) -> None:
        tenant = (self.tenant_id or "").strip()
        if not tenant:
            raise ValueError("ConversationMetadata requires tenant_id")


@dataclass(slots=True)
class ConversationSessionState:
    """State container describing the SDK session associated with a conversation."""

    provider: str | None = None
    provider_conversation_id: str | None = None
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
        tenant_id: str,
        metadata: ConversationMetadata,
    ) -> None: ...

    async def get_messages(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
    ) -> list[ConversationMessage]: ...

    async def list_conversation_ids(self, *, tenant_id: str) -> list[str]: ...

    async def iter_conversations(self, *, tenant_id: str) -> list[ConversationRecord]: ...

    async def paginate_conversations(
        self,
        *,
        tenant_id: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
        updated_after: datetime | None = None,
    ) -> ConversationPage: ...

    async def search_conversations(
        self,
        *,
        tenant_id: str,
        query: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
    ) -> ConversationSearchPage: ...

    async def clear_conversation(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
    ) -> None: ...

    async def get_session_state(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
    ) -> ConversationSessionState | None: ...

    async def upsert_session_state(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        state: ConversationSessionState,
    ) -> None: ...
