"""Pydantic models for conversation resources."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.api.v1.chat.schemas import MessageAttachment
from app.api.v1.shared.streaming import PublicSseEvent
from app.domain.conversation_titles import normalize_display_name


class ChatMessage(BaseModel):
    """Single conversational message."""

    message_id: str | None = Field(
        default=None,
        description="Stable identifier for this message (opaque string; safe for JS).",
    )
    role: Literal["user", "assistant", "system"] = Field(
        description="Originator of the message.",
    )
    content: str = Field(description="Message body.")
    timestamp: str | None = Field(
        default=None,
        description="ISO-8601 timestamp if available.",
    )
    attachments: list[MessageAttachment] = Field(
        default_factory=list,
        description="Attachments associated with this message (if any).",
    )


class ConversationHistory(BaseModel):
    """Full detail view of a conversation."""

    conversation_id: str = Field(description="Conversation identifier.")
    display_name: str | None = Field(default=None, description="Generated or assigned title.")
    messages: list[ChatMessage] = Field(description="Complete message history.")
    created_at: str = Field(description="Conversation creation timestamp.")
    updated_at: str = Field(description="Last update timestamp.")
    agent_context: dict[str, Any] | None = Field(
        default=None,
        description="Optional agent metadata.",
    )


class PaginatedMessagesResponse(BaseModel):
    """Paginated slice of messages for a conversation."""

    items: list[ChatMessage]
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor for fetching the next page.",
    )
    prev_cursor: str | None = Field(
        default=None,
        description="Opaque cursor for the previous page (not currently emitted).",
    )


class ConversationSummary(BaseModel):
    """Lightweight summary used when listing conversations."""

    conversation_id: str = Field(description="Conversation identifier.")
    display_name: str | None = Field(default=None, description="Generated conversation title.")
    agent_entrypoint: str | None = Field(
        default=None, description="Agent entrypoint configured for this thread."
    )
    active_agent: str | None = Field(
        default=None, description="Most recent agent that responded in the thread."
    )
    topic_hint: str | None = Field(default=None, description="Short title/topic if available.")
    status: str | None = Field(default=None, description="Lifecycle status (e.g., active).")
    message_count: int = Field(description="Number of messages recorded.")
    last_message_preview: str = Field(description="Content preview of the latest message.")
    created_at: str = Field(description="Creation timestamp.")
    updated_at: str = Field(description="Last update timestamp.")


class ConversationListResponse(BaseModel):
    """Paginated list of conversation summaries."""

    items: list[ConversationSummary]
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor for fetching the next page.",
    )


class ConversationSearchResult(BaseModel):
    """Search hit with preview and relevance score."""

    conversation_id: str = Field(description="Conversation identifier.")
    display_name: str | None = Field(default=None, description="Generated conversation title.")
    agent_entrypoint: str | None = Field(
        default=None, description="Agent entrypoint configured for this thread."
    )
    active_agent: str | None = Field(
        default=None, description="Most recent agent that responded in the thread."
    )
    topic_hint: str | None = Field(default=None, description="Short title/topic if available.")
    status: str | None = Field(default=None, description="Lifecycle status (e.g., active).")
    preview: str = Field(description="Matched message snippet.")
    last_message_preview: str | None = Field(
        default=None, description="Content preview of the latest message."
    )
    score: float | None = Field(default=None, description="Backend relevance score.")
    updated_at: str | None = Field(default=None, description="Last update timestamp.")


class ConversationMemoryConfigRequest(BaseModel):
    mode: Literal["none", "trim", "summarize", "compact"] | None = None
    max_user_turns: int | None = None
    keep_last_turns: int | None = None
    compact_trigger_turns: int | None = None
    compact_keep: int | None = None
    clear_tool_inputs: bool | None = None
    memory_injection: bool | None = None


class ConversationMemoryConfigResponse(ConversationMemoryConfigRequest):
    pass


class ConversationTitleUpdateRequest(BaseModel):
    """Request payload to rename a conversation title."""

    display_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User-defined conversation title.",
    )

    @field_validator("display_name", mode="before")
    @classmethod
    def _normalize_display_name(cls, value: object) -> str:
        if not isinstance(value, str):
            raise TypeError("display_name must be a string")
        return normalize_display_name(value)


class ConversationTitleUpdateResponse(BaseModel):
    """Response payload after updating a conversation title."""

    conversation_id: str = Field(description="Conversation identifier.")
    display_name: str = Field(description="Updated conversation title.")


class ConversationMessageDeleteResponse(BaseModel):
    """Response payload after truncating a conversation from a user message."""

    conversation_id: str = Field(description="Conversation identifier.")
    deleted_message_id: str = Field(description="User message id that triggered truncation.")
    success: bool = Field(default=True, description="Whether the truncation was applied.")


class ConversationSearchResponse(BaseModel):
    """Paginated search results."""

    items: list[ConversationSearchResult]
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor for fetching the next page of search results.",
    )


class ConversationEventItem(BaseModel):
    """Full-fidelity run item in a conversation."""

    sequence_no: int = Field(description="Monotonic sequence number within the conversation.")
    run_item_type: str = Field(
        description="Normalized item type (message, tool_call, tool_result, mcp_call, reasoning)."
    )
    run_item_name: str | None = Field(default=None, description="Provider-specific item name.")
    role: Literal["user", "assistant", "system"] | None = Field(default=None)
    agent: str | None = Field(default=None, description="Agent active when the item was created.")
    tool_call_id: str | None = Field(default=None)
    tool_name: str | None = Field(default=None)
    model: str | None = Field(default=None)
    content_text: str | None = Field(default=None)
    reasoning_text: str | None = Field(default=None)
    call_arguments: dict[str, Any] | None = Field(default=None)
    call_output: dict[str, Any] | None = Field(default=None)
    attachments: list[MessageAttachment] = Field(default_factory=list)
    response_id: str | None = Field(default=None)
    workflow_run_id: str | None = Field(
        default=None, description="Workflow run identifier when the event was produced."
    )
    timestamp: str = Field(description="ISO-8601 creation time of the item.")


class ConversationEventsResponse(BaseModel):
    """List of event-log items for a conversation."""

    conversation_id: str = Field(description="Conversation identifier.")
    items: list[ConversationEventItem]


class ConversationLedgerEventsResponse(BaseModel):
    """Paged list of persisted public_sse_v1 frames for deterministic UI replay."""

    conversation_id: str = Field(description="Conversation identifier.")
    items: list[PublicSseEvent]
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor for fetching the next page.",
    )


__all__ = [
    "ChatMessage",
    "ConversationHistory",
    "PaginatedMessagesResponse",
    "ConversationSummary",
    "ConversationListResponse",
    "ConversationSearchResult",
    "ConversationSearchResponse",
    "ConversationTitleUpdateRequest",
    "ConversationTitleUpdateResponse",
    "ConversationMessageDeleteResponse",
    "ConversationEventItem",
    "ConversationEventsResponse",
    "ConversationLedgerEventsResponse",
]
