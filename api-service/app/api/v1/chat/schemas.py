"""Schemas describing chat interactions with agents."""

from typing import Any, Literal

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


class StreamingChatEvent(BaseModel):
    """Rich streaming envelope forwarded over SSE to the frontend."""

    kind: Literal["raw_response", "run_item", "agent_update", "usage", "error"]

    conversation_id: str = Field(description="Conversation identifier.")
    agent_used: str | None = Field(default=None, description="Agent that produced the event.")

    response_id: str | None = Field(
        default=None,
        description="Upstream response id when available.",
    )
    sequence_number: int | None = Field(
        default=None,
        description="Sequence number from Responses API.",
    )

    raw_type: str | None = Field(
        default=None,
        description="Underlying Responses API event type.",
    )
    run_item_name: str | None = Field(
        default=None,
        description="RunItemStreamEvent name.",
    )
    run_item_type: str | None = Field(
        default=None,
        description="RunItem item.type.",
    )
    tool_call_id: str | None = Field(
        default=None,
        description="Tool call identifier if present.",
    )
    tool_name: str | None = Field(default=None, description="Tool name if present.")
    agent: str | None = Field(default=None, description="Agent associated with the event.")
    new_agent: str | None = Field(default=None, description="New agent after a handoff.")

    text_delta: str | None = Field(default=None, description="Streamed text chunk, if any.")
    reasoning_delta: str | None = Field(
        default=None,
        description="Streamed reasoning chunk, if any.",
    )
    is_terminal: bool = Field(default=False, description="Marks terminal event for the stream.")

    payload: dict[str, Any] | None = Field(
        default=None,
        description="Full event body for consumers that need raw fidelity.",
    )
