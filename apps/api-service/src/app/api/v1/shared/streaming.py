from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel

PUBLIC_SSE_SCHEMA_VERSION = "public_sse_v1"


# -----------------------------------------------------------------------------
# Shared primitives
# -----------------------------------------------------------------------------


class StreamNotice(BaseModel):
    """Explicit markers for UX when content is altered for safety/stability."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["redacted", "truncated"]
    path: str
    message: str


class WorkflowContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_key: str | None = None
    workflow_run_id: str | None = None
    stage_name: str | None = None
    step_name: str | None = None
    step_agent: str | None = None
    parallel_group: str | None = None
    branch_index: int | None = None


class MessageAttachment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_id: str = Field(description="Storage object identifier")
    filename: str = Field(description="Object filename")
    mime_type: str | None = Field(default=None, description="Mime type of the attachment")
    size_bytes: int | None = Field(default=None, description="Size in bytes")
    url: str | None = Field(default=None, description="Presigned download URL")
    tool_call_id: str | None = Field(default=None, description="Originating tool call id")


class PublicUsage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cached_input_tokens: int | None = None
    reasoning_output_tokens: int | None = None
    requests: int | None = None


class UrlCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["url_citation"] = "url_citation"
    start_index: int
    end_index: int
    title: str | None = None
    url: str


class ContainerFileCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["container_file_citation"] = "container_file_citation"
    start_index: int
    end_index: int
    container_id: str
    file_id: str
    filename: str | None = None
    url: str | None = None


class FileCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["file_citation"] = "file_citation"
    start_index: int | None = None
    end_index: int | None = None
    index: int | None = None
    file_id: str
    filename: str | None = None


PublicCitation = UrlCitation | ContainerFileCitation | FileCitation


# -----------------------------------------------------------------------------
# Tool payloads (derived-only, UX-oriented)
# -----------------------------------------------------------------------------


class WebSearchTool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_type: Literal["web_search"]
    tool_call_id: str
    status: Literal["in_progress", "searching", "completed"]
    query: str | None = None
    sources: list[str] | None = None


class FileSearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_id: str
    filename: str | None = None
    score: float | None = None
    vector_store_id: str | None = None
    attributes: dict[str, Any] | None = None
    text: str | None = None


class FileSearchTool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_type: Literal["file_search"]
    tool_call_id: str
    status: Literal["in_progress", "searching", "completed"]
    queries: list[str] | None = None
    results: list[FileSearchResult] | None = None


class CodeInterpreterTool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_type: Literal["code_interpreter"]
    tool_call_id: str
    status: Literal["in_progress", "interpreting", "completed"]
    container_id: str | None = None
    container_mode: Literal["auto", "explicit"] | None = None


class ImageGenerationTool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_type: Literal["image_generation"]
    tool_call_id: str
    status: Literal["in_progress", "generating", "partial_image", "completed"]
    revised_prompt: str | None = None
    format: str | None = None
    size: str | None = None
    quality: str | None = None
    background: str | None = None
    partial_image_index: int | None = None


class FunctionTool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_type: Literal["function"]
    tool_call_id: str
    status: Literal["in_progress", "completed", "failed"]
    name: str
    arguments_text: str | None = None
    arguments_json: dict[str, Any] | None = None
    output: Any | None = None


class McpTool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_type: Literal["mcp"]
    tool_call_id: str
    status: Literal["awaiting_approval", "in_progress", "completed", "failed"]
    tool_name: str
    server_label: str | None = None
    arguments_text: str | None = None
    arguments_json: dict[str, Any] | None = None
    output: Any | None = None


PublicTool = (
    WebSearchTool
    | FileSearchTool
    | CodeInterpreterTool
    | ImageGenerationTool
    | FunctionTool
    | McpTool
)


# -----------------------------------------------------------------------------
# Events (discriminated by `kind`)
# -----------------------------------------------------------------------------


class PublicSseEventBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # `schema` is part of the public wire contract, but `BaseModel` already has a
    # `.schema()` helper; keep the JSON field name while avoiding attribute shadowing.
    schema_: Literal["public_sse_v1"] = Field(alias="schema")
    event_id: int
    stream_id: str
    server_timestamp: str

    conversation_id: str
    response_id: str | None = None
    agent: str | None = None
    workflow: WorkflowContext | None = None

    provider_sequence_number: int | None = None
    notices: list[StreamNotice] | None = None


class PublicSseItemEventBase(PublicSseEventBase):
    """Event scoped to a single Responses output item."""

    output_index: int = Field(description="Index into the provider response.output[] array.")
    item_id: str = Field(description="Stable identifier of the provider output item.")


class LifecycleEvent(PublicSseEventBase):
    kind: Literal["lifecycle"]
    status: Literal["queued", "in_progress", "completed", "failed", "incomplete", "cancelled"]
    reason: str | None = None


class OutputItemAddedEvent(PublicSseItemEventBase):
    kind: Literal["output_item.added"]
    item_type: str
    role: str | None = None
    status: str | None = None


class OutputItemDoneEvent(PublicSseItemEventBase):
    kind: Literal["output_item.done"]
    item_type: str
    role: str | None = None
    status: str | None = None


class MessageDeltaEvent(PublicSseItemEventBase):
    kind: Literal["message.delta"]
    content_index: int
    delta: str


class MessageCitationEvent(PublicSseItemEventBase):
    kind: Literal["message.citation"]
    content_index: int
    citation: PublicCitation


class ReasoningSummaryDeltaEvent(PublicSseItemEventBase):
    kind: Literal["reasoning_summary.delta"]
    summary_index: int | None = None
    delta: str


class RefusalDeltaEvent(PublicSseItemEventBase):
    kind: Literal["refusal.delta"]
    content_index: int
    delta: str


class RefusalDoneEvent(PublicSseItemEventBase):
    kind: Literal["refusal.done"]
    content_index: int
    refusal_text: str


class ToolStatusEvent(PublicSseItemEventBase):
    kind: Literal["tool.status"]
    tool: PublicTool


class ToolArgumentsDeltaEvent(PublicSseItemEventBase):
    kind: Literal["tool.arguments.delta"]
    tool_call_id: str
    tool_type: Literal["function", "mcp"]
    tool_name: str
    delta: str


class ToolArgumentsDoneEvent(PublicSseItemEventBase):
    kind: Literal["tool.arguments.done"]
    tool_call_id: str
    tool_type: Literal["function", "mcp"]
    tool_name: str
    arguments_text: str
    arguments_json: dict[str, Any] | None = None


class ToolCodeDeltaEvent(PublicSseItemEventBase):
    kind: Literal["tool.code.delta"]
    tool_call_id: str
    delta: str


class ToolCodeDoneEvent(PublicSseItemEventBase):
    kind: Literal["tool.code.done"]
    tool_call_id: str
    code: str


class ToolOutputEvent(PublicSseItemEventBase):
    kind: Literal["tool.output"]
    tool_call_id: str
    tool_type: Literal[
        "web_search",
        "file_search",
        "code_interpreter",
        "image_generation",
        "function",
        "mcp",
    ]
    output: Any


class ChunkTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_kind: Literal["tool_call", "message"]
    entity_id: str
    field: str
    part_index: int | None = None


class ChunkDeltaEvent(PublicSseItemEventBase):
    kind: Literal["chunk.delta"]
    target: ChunkTarget
    encoding: Literal["base64", "utf8"] = "utf8"
    chunk_index: int
    data: str


class ChunkDoneEvent(PublicSseItemEventBase):
    kind: Literal["chunk.done"]
    target: ChunkTarget


class ErrorPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str | None = None
    message: str
    source: Literal["provider", "server"]
    is_retryable: bool


class ErrorEvent(PublicSseEventBase):
    kind: Literal["error"]
    error: ErrorPayload


class FinalPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["completed", "failed", "incomplete", "refused", "cancelled"]
    response_text: str | None = None
    structured_output: Any | None = None
    reasoning_summary_text: str | None = None
    refusal_text: str | None = None
    attachments: list[MessageAttachment] = Field(default_factory=list)
    usage: PublicUsage | None = None


class FinalEvent(PublicSseEventBase):
    kind: Literal["final"]
    final: FinalPayload


PublicSseEventUnion = (
    LifecycleEvent
    | OutputItemAddedEvent
    | OutputItemDoneEvent
    | MessageDeltaEvent
    | MessageCitationEvent
    | ReasoningSummaryDeltaEvent
    | RefusalDeltaEvent
    | RefusalDoneEvent
    | ToolStatusEvent
    | ToolArgumentsDeltaEvent
    | ToolArgumentsDoneEvent
    | ToolCodeDeltaEvent
    | ToolCodeDoneEvent
    | ToolOutputEvent
    | ChunkDeltaEvent
    | ChunkDoneEvent
    | ErrorEvent
    | FinalEvent
)


class PublicSseEvent(RootModel[PublicSseEventUnion]):
    """Root model so the wire format is the event object itself (not nested)."""

    model_config = ConfigDict(title="PublicSseEvent")


__all__ = [
    "PUBLIC_SSE_SCHEMA_VERSION",
    "ChunkDeltaEvent",
    "ChunkDoneEvent",
    "ChunkTarget",
    "CodeInterpreterTool",
    "ContainerFileCitation",
    "OutputItemAddedEvent",
    "OutputItemDoneEvent",
    "ErrorEvent",
    "ErrorPayload",
    "FileCitation",
    "FileSearchResult",
    "FileSearchTool",
    "FinalEvent",
    "FinalPayload",
    "FunctionTool",
    "ImageGenerationTool",
    "LifecycleEvent",
    "McpTool",
    "MessageAttachment",
    "MessageCitationEvent",
    "MessageDeltaEvent",
    "PublicCitation",
    "PublicSseEvent",
    "PublicTool",
    "PublicUsage",
    "ReasoningSummaryDeltaEvent",
    "RefusalDeltaEvent",
    "RefusalDoneEvent",
    "StreamNotice",
    "ToolArgumentsDeltaEvent",
    "ToolArgumentsDoneEvent",
    "ToolCodeDeltaEvent",
    "ToolCodeDoneEvent",
    "ToolOutputEvent",
    "ToolStatusEvent",
    "UrlCitation",
    "WebSearchTool",
    "WorkflowContext",
]
