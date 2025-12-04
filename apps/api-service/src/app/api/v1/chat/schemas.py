"""Schemas describing chat interactions with agents."""

from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict


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
    raw_event: dict[str, Any] | None = Field(
        default=None,
        description="Original upstream event payload (for audit/forward-compat).",
    )

    # Tool calls (typed surface; currently web_search)
    tool_call: "ToolCallPayload | dict[str, Any] | None" = Field(
        default=None,
        description="Typed tool call payload (e.g., web_search_call).",
    )

    # Output annotations (e.g., citations)
    annotations: list["UrlCitation | ContainerFileCitation | FileCitation"] | None = Field(
        default=None,
        description="Inline annotations such as URL citations emitted with output_text.",
    )


class MessageAttachment(BaseModel):
    object_id: str = Field(description="Storage object identifier")
    filename: str = Field(description="Object filename")
    mime_type: str | None = Field(default=None, description="Mime type of the attachment")
    size_bytes: int | None = Field(default=None, description="Size in bytes")
    url: str | None = Field(default=None, description="Presigned download URL")
    tool_call_id: str | None = Field(default=None, description="Originating tool call id")


# ---------- Tool & annotation payloads ----------

class WebSearchAction(BaseModel):
    type: Literal["search"]
    query: str
    sources: list[str] | None = None


class WebSearchCall(BaseModel):
    id: str
    type: Literal["web_search_call"]
    status: Literal["in_progress", "completed"]
    action: WebSearchAction | None = None


class CodeInterpreterCall(BaseModel):
    id: str
    type: Literal["code_interpreter_call"]
    status: Literal["in_progress", "interpreting", "completed"]
    code: str | None = None
    outputs: list[Any] | None = None


class FileSearchCall(BaseModel):
    id: str
    type: Literal["file_search_call"]
    status: Literal["in_progress", "searching", "completed"]
    queries: list[str] | None = None
    results: list[Any] | None = None


class ToolCallPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    tool_type: str
    web_search_call: WebSearchCall | None = None
    code_interpreter_call: CodeInterpreterCall | None = None
    file_search_call: FileSearchCall | None = None


class UrlCitation(BaseModel):
    type: Literal["url_citation"] = "url_citation"
    start_index: int
    end_index: int
    title: str | None = None
    url: str


class ContainerFileCitation(BaseModel):
    type: Literal["container_file_citation"] = "container_file_citation"
    start_index: int
    end_index: int
    container_id: str
    file_id: str
    filename: str | None = None
    url: str | None = None  # optional presigned URL if provided upstream


class FileCitation(BaseModel):
    type: Literal["file_citation"] = "file_citation"
    start_index: int | None = None
    end_index: int | None = None
    index: int | None = None
    file_id: str
    filename: str | None = None


AgentChatRequest.model_rebuild()
AgentChatResponse.model_rebuild()
StreamingChatEvent.model_rebuild()
