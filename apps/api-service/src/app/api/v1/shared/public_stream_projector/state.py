from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ..streaming import FileSearchResult, MessageAttachment

LifecycleStatus = Literal[
    "queued",
    "in_progress",
    "completed",
    "failed",
    "incomplete",
    "cancelled",
]

ToolType = Literal[
    "web_search",
    "file_search",
    "code_interpreter",
    "image_generation",
    "function",
    "mcp",
]

ArgsToolType = Literal["function", "mcp"]
SearchStatus = Literal["in_progress", "searching", "completed"]
CodeInterpreterStatus = Literal["in_progress", "interpreting", "completed"]
ImageGenerationStatus = Literal["in_progress", "generating", "partial_image", "completed"]
FinalStatus = Literal["completed", "failed", "incomplete", "refused", "cancelled"]


@dataclass(slots=True)
class ToolState:
    tool_type: ToolType
    output_index: int | None = None
    tool_name: str | None = None
    query: str | None = None
    sources: list[str] | None = None
    server_label: str | None = None
    last_status: str | None = None
    arguments_text: str = ""
    file_search_queries: list[str] | None = None
    file_search_results: list[FileSearchResult] | None = None
    container_id: str | None = None
    container_mode: Literal["auto", "explicit"] | None = None
    image_revised_prompt: str | None = None
    image_format: str | None = None
    image_size: str | None = None
    image_quality: str | None = None
    image_background: str | None = None
    image_partial_image_index: int | None = None


@dataclass(slots=True)
class ProjectionState:
    event_id: int = 0
    lifecycle_status: LifecycleStatus | None = None
    reasoning_summary_text: str = ""
    refusal_text: str = ""
    tool_state: dict[str, ToolState] = field(default_factory=dict)
    last_web_search_tool_call_id: str | None = None
    attachments: list[MessageAttachment] = field(default_factory=list)
    seen_attachment_ids: set[str] = field(default_factory=set)
    terminal_emitted: bool = False

