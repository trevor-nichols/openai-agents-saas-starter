"""Schemas describing chat interactions with agents."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class LocationHint(BaseModel):
    """Optional coarse location provided by the user/tenant for web search biasing."""

    city: str | None = Field(default=None, description="City name (coarse, e.g., 'Austin').")
    region: str | None = Field(
        default=None,
        description="Region/subdivision (e.g., state/province) for coarse location.",
    )
    country: str | None = Field(
        default=None,
        description="Country code or name for coarse location.",
    )
    timezone: str | None = Field(
        default=None,
        description="IANA timezone identifier if relevant to the query.",
    )


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
    share_location: bool = Field(
        default=False,
        description=(
            "When true, allows the assistant to use provided coarse location for web search."
        ),
    )
    location: LocationHint | None = Field(
        default=None,
        description=(
            "Optional coarse location (city/region/country/timezone) for location-biased search."
        ),
    )
    run_options: "RunOptionsRequest | None" = Field(
        default=None,
        description="Advanced controls (max_turns, previous_response_id, run_config, hooks).",
    )


class AgentChatResponse(BaseModel):
    """Response body returned after the agent processes a message."""

    response: str = Field(description="Natural language reply from the agent.")
    structured_output: Any | None = Field(
        default=None,
        description="If the agent used structured outputs, this carries the parsed object.",
    )
    conversation_id: str = Field(description="Conversation identifier.")
    agent_used: str = Field(description="Agent instance that handled the request.")
    handoff_occurred: bool = Field(
        default=False,
        description="Indicates whether a handoff happened mid-conversation.",
    )
    attachments: list["MessageAttachment"] = Field(
        default_factory=list,
        description="Attachments created during the response (e.g., generated images).",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary metadata returned by the agent pipeline.",
    )


class StreamingChatEvent(BaseModel):
    """Rich streaming envelope forwarded over SSE to the frontend."""

    kind: Literal[
        "raw_response_event",
        "run_item_stream_event",
        "agent_updated_stream_event",
        "usage",
        "error",
        "lifecycle",
    ]

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
    response_text: Any | None = Field(
        default=None,
        description=(
            "Final rendered response text when no deltas are sent "
            "(e.g., structured outputs)."
        ),
    )
    structured_output: Any | None = Field(
        default=None,
        description="Parsed structured output when provided by the agent.",
    )
    is_terminal: bool = Field(default=False, description="Marks terminal event for the stream.")

    event: str | None = Field(
        default=None,
        description="Lifecycle event label emitted via hooks (e.g., agent_start, handoff).",
    )

    payload: dict[str, Any] | None = Field(
        default=None,
        description="Full event body for consumers that need raw fidelity.",
    )
    attachments: list["MessageAttachment"] | None = Field(
        default=None,
        description="Attachments generated during this event (e.g., stored images).",
    )


class RunOptionsRequest(BaseModel):
    """Optional advanced controls forwarded to the Agents SDK."""

    max_turns: int | None = Field(
        default=None, description="Override max agent turns for this run (default SDK limit)."
    )
    previous_response_id: str | None = Field(
        default=None,
        description="Responses API previous_response_id to continue without resending history.",
    )
    handoff_input_filter: str | None = Field(
        default=None,
        description="Named handoff input filter to apply globally (provider-defined registry).",
    )
    run_config: dict[str, Any] | None = Field(
        default=None,
        description="Raw RunConfig overrides (provider-specific).",
    )


class MessageAttachment(BaseModel):
    object_id: str = Field(description="Storage object identifier")
    filename: str = Field(description="Object filename")
    mime_type: str | None = Field(default=None, description="Mime type of the attachment")
    size_bytes: int | None = Field(default=None, description="Size in bytes")
    url: str | None = Field(default=None, description="Presigned download URL")
    tool_call_id: str | None = Field(default=None, description="Originating tool call id")


AgentChatRequest.model_rebuild()
AgentChatResponse.model_rebuild()
StreamingChatEvent.model_rebuild()
