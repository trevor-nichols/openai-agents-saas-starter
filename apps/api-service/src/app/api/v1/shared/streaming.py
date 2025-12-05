from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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
    results: list[FileSearchResult] | None = None


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


class FileSearchResult(BaseModel):
    file_id: str
    filename: str | None = None
    score: float | None = None
    vector_store_id: str | None = None
    attributes: dict[str, Any] | None = None
    text: str | None = None


class StreamingEvent(BaseModel):
    kind: Literal[
        "raw_response_event",
        "run_item_stream_event",
        "agent_updated_stream_event",
        "usage",
        "error",
        "lifecycle",
    ]
    # Workflow metadata (optional for agent streams)
    workflow_key: str | None = None
    workflow_run_id: str | None = None
    step_name: str | None = None
    step_agent: str | None = None
    stage_name: str | None = None
    parallel_group: str | None = None
    branch_index: int | None = None

    # Conversation/agent metadata
    conversation_id: str | None = None
    agent_used: str | None = None
    response_id: str | None = None
    sequence_number: int | None = None
    raw_type: str | None = None
    run_item_name: str | None = None
    run_item_type: str | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    agent: str | None = None
    new_agent: str | None = None

    # Content
    text_delta: str | None = None
    reasoning_delta: str | None = None
    response_text: str | None = None
    structured_output: Any | None = None
    is_terminal: bool = False
    event: str | None = None
    payload: dict[str, Any] | None = None
    attachments: list[MessageAttachment | dict[str, Any]] | None = None
    raw_event: dict[str, Any] | None = None
    tool_call: ToolCallPayload | dict[str, Any] | None = None
    annotations: list[UrlCitation | ContainerFileCitation | FileCitation] | None = None
    server_timestamp: str | None = None


__all__ = [
    "StreamingEvent",
    "MessageAttachment",
    "WebSearchAction",
    "WebSearchCall",
    "CodeInterpreterCall",
    "FileSearchCall",
    "ToolCallPayload",
    "UrlCitation",
    "ContainerFileCitation",
    "FileCitation",
    "FileSearchResult",
]
