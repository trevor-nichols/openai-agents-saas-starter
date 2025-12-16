"""Tool-call normalization helpers for OpenAI streaming events."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.utils.tools.builtin_tools import infer_builtin_tool_name


def coerce_delta(delta: Any) -> str:
    if delta is None:
        return ""
    if isinstance(delta, str):
        return delta
    try:
        return str(delta)
    except Exception:  # pragma: no cover - extremely defensive
        return ""


def build_web_search_tool_call(
    *,
    item_id: Any,
    status: str | None,
    action: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    normalized_status = "in_progress"
    if status in {"searching", "completed"}:
        normalized_status = status
    return {
        "tool_type": "web_search",
        "web_search_call": {
            "id": str(item_id) if item_id is not None else "",
            "type": "web_search_call",
            "status": normalized_status,
            "action": action,
        },
    }


def build_code_interpreter_tool_call(
    *,
    item_id: Any,
    status: str | None,
    code: str | None = None,
    outputs: Any | None = None,
    container_id: str | None = None,
    container_mode: str | None = None,
    annotations: list[Mapping[str, Any]] | None = None,
) -> Mapping[str, Any]:
    normalized_status = "in_progress"
    if status in {"completed", "interpreting"}:
        normalized_status = status
    return {
        "tool_type": "code_interpreter",
        "code_interpreter_call": {
            "id": str(item_id) if item_id is not None else "",
            "type": "code_interpreter_call",
            "status": normalized_status,
            "code": code,
            "outputs": outputs,
            "container_id": container_id,
            "container_mode": container_mode,
            "annotations": annotations,
        },
    }


def build_file_search_tool_call(
    *,
    item_id: Any,
    status: str | None,
    queries: list[str] | None = None,
    results: Any | None = None,
) -> Mapping[str, Any]:
    normalized_status = "in_progress"
    if status in {"searching", "completed"}:
        normalized_status = status
    return {
        "tool_type": "file_search",
        "file_search_call": {
            "id": str(item_id) if item_id is not None else "",
            "type": "file_search_call",
            "status": normalized_status,
            "queries": queries,
            "results": results,
        },
    }


def build_image_generation_tool_call(
    *,
    item_id: Any,
    status: str | None,
    result: Any | None = None,
    revised_prompt: str | None = None,
    image_format: str | None = None,
    size: str | None = None,
    quality: str | None = None,
    background: str | None = None,
    output_index: int | None = None,
    partial_image_index: int | None = None,
    partial_image_b64: str | None = None,
) -> Mapping[str, Any]:
    normalized_status = (
        status
        if status in {"in_progress", "generating", "partial_image", "completed"}
        else "in_progress"
    )
    return {
        "tool_type": "image_generation",
        "image_generation_call": {
            "id": str(item_id) if item_id is not None else "",
            "type": "image_generation_call",
            "status": normalized_status,
            "result": result,
            "revised_prompt": revised_prompt,
            "format": image_format,
            "size": size,
            "quality": quality,
            "background": background,
            "output_index": output_index,
            "partial_image_index": partial_image_index,
            "partial_image_b64": partial_image_b64,
            # Some Responses events surface partials as b64_json; keep alias for clients.
            "b64_json": partial_image_b64 if partial_image_b64 else None,
        },
    }


def extract_agent_name(obj: Any) -> str | None:
    if obj is None:
        return None
    name = getattr(obj, "name", None)
    if isinstance(name, str):
        return name
    agent = getattr(obj, "agent", None)
    agent_name = getattr(agent, "name", None)
    return agent_name if isinstance(agent_name, str) else None


def extract_tool_info(item: Any) -> tuple[str | None, str | None]:
    if item is None:
        return None, None
    raw_item = getattr(item, "raw_item", None)
    tool_call_id = getattr(raw_item, "id", None) or getattr(item, "id", None)
    tool_name = getattr(raw_item, "name", None) or getattr(item, "name", None)
    if tool_name is None:
        raw_item_type = getattr(raw_item, "type", None)
        item_type = getattr(item, "type", None)
        tool_name = infer_builtin_tool_name(raw_item_type) or infer_builtin_tool_name(item_type)
    if tool_call_id is not None:
        tool_call_id = str(tool_call_id)
    if tool_name is not None:
        tool_name = str(tool_name)
    return tool_call_id, tool_name


__all__ = [
    "coerce_delta",
    "build_web_search_tool_call",
    "build_code_interpreter_tool_call",
    "build_file_search_tool_call",
    "build_image_generation_tool_call",
    "extract_agent_name",
    "extract_tool_info",
]
