"""Schemas describing chat interactions with agents."""

from typing import Any

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """Request body for initiating or continuing a chat session."""

    message: str = Field(description="User input message for the agent.")
    conversation_id: str | None = Field(
        default=None,
        description="Existing conversation identifier to maintain context.",
    )
    agent_type: str | None = Field(
        default="triage",
        description="Optional explicit agent to handle the message.",
    )
    context: dict[str, Any] | None = Field(
        default=None,
        description="Optional, structured context to pass through.",
    )


class AgentChatResponse(BaseModel):
    """Response body returned after the agent processes a message."""

    response: str = Field(description="Natural language reply from the agent.")
    conversation_id: str = Field(description="Conversation identifier.")
    agent_used: str = Field(description="Agent instance that handled the request.")
    handoff_occurred: bool = Field(
        default=False,
        description="Indicates whether a handoff happened mid-conversation.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary metadata returned by the agent pipeline.",
    )


class StreamingChatResponse(BaseModel):
    """Envelope emitted for each streamed chunk in SSE responses."""

    chunk: str = Field(description="Partial content from the agent.")
    conversation_id: str = Field(description="Conversation identifier.")
    is_complete: bool = Field(
        default=False,
        description="Signals completion when True.",
    )
    agent_used: str | None = Field(
        default=None,
        description="Agent instance that produced the chunk.",
    )
