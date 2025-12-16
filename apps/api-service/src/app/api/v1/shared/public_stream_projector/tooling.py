from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, cast

from ..streaming import FileSearchResult, StreamNotice
from .sanitize import truncate_string
from .state import (
    ArgsToolType,
    CodeInterpreterStatus,
    ImageGenerationStatus,
    ProjectionState,
    SearchStatus,
    ToolState,
    ToolType,
)
from .utils import as_dict, coerce_str


def as_search_status(value: str | None) -> SearchStatus:
    if value in {"in_progress", "searching", "completed"}:
        return cast(SearchStatus, value)
    return "in_progress"


def as_code_interpreter_status(value: str | None) -> CodeInterpreterStatus:
    if value in {"in_progress", "interpreting", "completed"}:
        return cast(CodeInterpreterStatus, value)
    return "in_progress"


def as_image_generation_status(value: str | None) -> ImageGenerationStatus:
    if value in {"in_progress", "generating", "partial_image", "completed"}:
        return cast(ImageGenerationStatus, value)
    return "in_progress"


def coerce_file_search_results(
    results: Any,
    *,
    max_results: int = 10,
    max_text_chars: int = 2_000,
) -> tuple[list[FileSearchResult] | None, list[StreamNotice]]:
    if not isinstance(results, list):
        return None, []

    coerced: list[FileSearchResult] = []
    notices: list[StreamNotice] = []
    for idx, item in enumerate(results[:max_results]):
        if not isinstance(item, dict):
            continue
        try:
            result = FileSearchResult.model_validate(item)
        except Exception:
            continue
        if isinstance(result.text, str):
            truncated, notice = truncate_string(
                value=result.text,
                path=f"tool.results[{idx}].text",
                max_chars=max_text_chars,
            )
            if notice:
                notices.append(notice)
                result = result.model_copy(update={"text": truncated})
        coerced.append(result)

    if len(results) > max_results:
        notices.append(
            StreamNotice(
                type="truncated",
                path="tool.results",
                message=f"Results list truncated to {max_results} items.",
            )
        )
    return (coerced or None), notices


def merge_tool_call_into_state(
    state: ProjectionState, tool_call: Mapping[str, Any]
) -> tuple[str, ToolType, str | None, list[StreamNotice]] | None:
    tool_type = tool_call.get("tool_type")
    if tool_type == "web_search":
        call = as_dict(tool_call.get("web_search_call")) or {}
        tool_call_id = coerce_str(call.get("id"))
        if not tool_call_id:
            return None
        status = coerce_str(call.get("status"))
        tool_state = state.tool_state.setdefault(tool_call_id, ToolState(tool_type="web_search"))
        if status:
            tool_state.last_status = status
        action = as_dict(call.get("action")) or {}
        query = coerce_str(action.get("query"))
        if query:
            tool_state.query = query
        state.last_web_search_tool_call_id = tool_call_id
        return tool_call_id, "web_search", status, []

    if tool_type == "file_search":
        call = as_dict(tool_call.get("file_search_call")) or {}
        tool_call_id = coerce_str(call.get("id"))
        if not tool_call_id:
            return None
        status = coerce_str(call.get("status"))
        tool_state = state.tool_state.setdefault(tool_call_id, ToolState(tool_type="file_search"))
        if status:
            tool_state.last_status = status
        queries = call.get("queries")
        if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
            tool_state.file_search_queries = [q for q in queries if q]
        results, notices = coerce_file_search_results(call.get("results"))
        if results is not None:
            tool_state.file_search_results = results
        return tool_call_id, "file_search", status, notices

    if tool_type == "code_interpreter":
        call = as_dict(tool_call.get("code_interpreter_call")) or {}
        tool_call_id = coerce_str(call.get("id"))
        if not tool_call_id:
            return None
        status = coerce_str(call.get("status"))
        tool_state = state.tool_state.setdefault(
            tool_call_id,
            ToolState(tool_type="code_interpreter"),
        )
        if status:
            tool_state.last_status = status
        tool_state.container_id = coerce_str(call.get("container_id")) or tool_state.container_id
        container_mode = coerce_str(call.get("container_mode"))
        if container_mode in {"auto", "explicit"}:
            tool_state.container_mode = cast(Literal["auto", "explicit"], container_mode)
        return tool_call_id, "code_interpreter", status, []

    if tool_type == "image_generation":
        call = as_dict(tool_call.get("image_generation_call")) or {}
        tool_call_id = coerce_str(call.get("id"))
        if not tool_call_id:
            return None
        status = coerce_str(call.get("status"))
        tool_state = state.tool_state.setdefault(
            tool_call_id,
            ToolState(tool_type="image_generation"),
        )
        if status:
            tool_state.last_status = status
        tool_state.image_revised_prompt = (
            coerce_str(call.get("revised_prompt")) or tool_state.image_revised_prompt
        )
        tool_state.image_format = coerce_str(call.get("format")) or tool_state.image_format
        tool_state.image_size = coerce_str(call.get("size")) or tool_state.image_size
        tool_state.image_quality = coerce_str(call.get("quality")) or tool_state.image_quality
        tool_state.image_background = (
            coerce_str(call.get("background")) or tool_state.image_background
        )
        partial_index = call.get("partial_image_index")
        if isinstance(partial_index, int):
            tool_state.image_partial_image_index = partial_index
        return tool_call_id, "image_generation", status, []

    return None


def args_tool_type_from_raw_type(raw_type: str) -> ArgsToolType:
    return "mcp" if "mcp_" in raw_type else "function"


def tool_name_from_run_item(raw_item: dict[str, Any] | None) -> str | None:
    if not raw_item:
        return None
    # Function tools: raw_item.name
    name = raw_item.get("name")
    if isinstance(name, str) and name:
        return name
    # Hosted tools: infer from raw_item.type
    raw_type = raw_item.get("type")
    if raw_type == "web_search_call":
        return "web_search"
    if raw_type == "file_search_call":
        return "file_search"
    if raw_type == "code_interpreter_call":
        return "code_interpreter"
    if raw_type == "image_generation_call":
        return "image_generation"
    return None
