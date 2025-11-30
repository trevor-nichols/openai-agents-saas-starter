"""Domain models and contracts for conversation data."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol


class ConversationNotFoundError(RuntimeError):
    """Raised when a conversation lookup fails for the given tenant."""


@dataclass(slots=True)
class ConversationMessage:
    """Domain representation of a single conversational message."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    attachments: list[ConversationAttachment] = field(default_factory=list)


@dataclass(slots=True)
class ConversationAttachment:
    """Attachment metadata linked to a message (e.g., generated image)."""

    object_id: str
    filename: str
    mime_type: str | None = None
    size_bytes: int | None = None
    presigned_url: str | None = None
    tool_call_id: str | None = None


@dataclass(slots=True)
class ConversationEvent:
    """Full-fidelity run item captured during an agent interaction."""

    run_item_type: str
    run_item_name: str | None = None
    role: Literal["user", "assistant", "system"] | None = None
    agent: str | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    model: str | None = None
    content_text: str | None = None
    reasoning_text: str | None = None
    call_arguments: Mapping[str, object] | None = None
    call_output: Mapping[str, object] | None = None
    attachments: list[ConversationAttachment] = field(default_factory=list)
    response_id: str | None = None
    sequence_no: int | None = None
    workflow_run_id: str | None = None
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

    async def add_run_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        events: list[ConversationEvent],
    ) -> None: ...

    async def get_run_events(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        include_types: set[str] | None = None,
        workflow_run_id: str | None = None,
    ) -> list[ConversationEvent]: ...
