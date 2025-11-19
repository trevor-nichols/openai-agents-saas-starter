"""Pydantic models for conversation resources."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single conversational message."""

    role: Literal["user", "assistant", "system"] = Field(
        description="Originator of the message.",
    )
    content: str = Field(description="Message body.")
    timestamp: str | None = Field(
        default=None,
        description="ISO-8601 timestamp if available.",
    )


class ConversationHistory(BaseModel):
    """Full detail view of a conversation."""

    conversation_id: str = Field(description="Conversation identifier.")
    messages: list[ChatMessage] = Field(description="Complete message history.")
    created_at: str = Field(description="Conversation creation timestamp.")
    updated_at: str = Field(description="Last update timestamp.")
    agent_context: dict[str, Any] | None = Field(
        default=None,
        description="Optional agent metadata.",
    )


class ConversationSummary(BaseModel):
    """Lightweight summary used when listing conversations."""

    conversation_id: str = Field(description="Conversation identifier.")
    message_count: int = Field(description="Number of messages recorded.")
    last_message: str = Field(description="Content preview of the latest message.")
    created_at: str = Field(description="Creation timestamp.")
    updated_at: str = Field(description="Last update timestamp.")
