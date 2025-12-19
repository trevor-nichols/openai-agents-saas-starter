"""Domain models and contracts for conversation data."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol


class ConversationNotFoundError(RuntimeError):
    """Raised when a conversation lookup fails for the given tenant."""


class ConversationMessageNotFoundError(RuntimeError):
    """Raised when a message lookup fails for the given conversation."""


class ConversationMessageNotDeletableError(RuntimeError):
    """Raised when a requested message cannot be deleted (e.g., not a user message)."""


@dataclass(slots=True)
class ConversationMessage:
    """Domain representation of a single conversational message."""

    role: Literal["user", "assistant", "system"]
    content: str
    message_id: str | None = None
    position: int | None = None
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
    """Aggregate containing an identifier, its message history, and metadata."""

    conversation_id: str
    messages: list[ConversationMessage]
    display_name: str | None = None
    agent_entrypoint: str | None = None
    active_agent: str | None = None
    topic_hint: str | None = None
    status: str | None = None
    title_generated_at: datetime | None = None
    created_at_value: datetime | None = None
    updated_at_value: datetime | None = None

    @property
    def created_at(self) -> datetime:
        if self.created_at_value:
            return self.created_at_value
        return self.messages[0].timestamp if self.messages else datetime.utcnow()

    @property
    def updated_at(self) -> datetime:
        if self.updated_at_value:
            return self.updated_at_value
        return self.messages[-1].timestamp if self.messages else datetime.utcnow()


@dataclass(slots=True)
class ConversationPage:
    """Page of conversations plus a cursor for keyset pagination."""

    items: list[ConversationRecord]
    next_cursor: str | None


@dataclass(slots=True)
class MessagePage:
    """Page of messages within a conversation plus a cursor."""

    items: list[ConversationMessage]
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


@dataclass(slots=True)
class ConversationMemoryConfig:
    """Persisted memory strategy defaults for a conversation."""

    strategy: str | None = None
    max_user_turns: int | None = None
    keep_last_turns: int | None = None
    compact_trigger_turns: int | None = None
    compact_keep: int | None = None
    clear_tool_inputs: bool | None = None
    memory_injection: bool | None = None


@dataclass(slots=True)
class ConversationSummary:
    """Cross-session summary snapshot."""

    conversation_id: str
    agent_key: str | None
    summary_text: str
    summary_model: str | None = None
    summary_length_tokens: int | None = None
    version: str | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class ConversationRunUsage:
    """Per-run usage record for audit/analytics."""

    conversation_id: str
    response_id: str | None
    run_id: str | None
    agent_key: str | None
    provider: str | None
    requests: int | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    cached_input_tokens: int | None
    reasoning_output_tokens: int | None
    request_usage_entries: list[Mapping[str, Any]] | None
    created_at: datetime


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

    async def paginate_messages(
        self,
        *,
        conversation_id: str,
        tenant_id: str,
        limit: int,
        cursor: str | None = None,
        direction: Literal["asc", "desc"] = "desc",
    ) -> MessagePage: ...

    async def search_conversations(
        self,
        *,
        tenant_id: str,
        query: str,
        limit: int,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
    ) -> ConversationSearchPage: ...

    async def get_conversation(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
    ) -> ConversationRecord | None: ...

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
        workflow_run_id: str | None = None,
    ) -> list[ConversationEvent]: ...

    async def get_memory_config(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
    ) -> ConversationMemoryConfig | None: ...

    async def set_memory_config(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        config: ConversationMemoryConfig,
        provided_fields: set[str] | None = None,
    ) -> None: ...

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
    ) -> None: ...

    async def get_latest_summary(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        agent_key: str | None,
        max_age_seconds: int | None = None,
    ) -> ConversationSummary | None: ...

    async def add_run_usage(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        usage: ConversationRunUsage,
    ) -> None: ...

    async def list_run_usage(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        limit: int = 20,
    ) -> list[ConversationRunUsage]: ...

    async def set_display_name(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        display_name: str,
        generated_at: datetime | None = None,
    ) -> bool: ...

    async def update_display_name(
        self,
        conversation_id: str,
        *,
        tenant_id: str,
        display_name: str,
    ) -> None: ...


__all__ = [
    "ConversationAttachment",
    "ConversationEvent",
    "ConversationMessage",
    "ConversationMetadata",
    "ConversationNotFoundError",
    "ConversationMessageNotDeletableError",
    "ConversationMessageNotFoundError",
    "ConversationPage",
    "ConversationRecord",
    "ConversationRepository",
    "ConversationSearchHit",
    "ConversationSearchPage",
    "ConversationSessionState",
    "ConversationMemoryConfig",
    "ConversationSummary",
    "ConversationRunUsage",
    "MessagePage",
]
