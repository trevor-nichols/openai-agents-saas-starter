"""Helpers for mapping built-in Responses API tool item types to stable names.

The OpenAI Responses API emits tool run items like `web_search_call` without a `name`.
Downstream (UI + event log) expects a human-friendly, stable tool name like `web_search`.
"""

from __future__ import annotations

from typing import Final

BUILTIN_TOOL_NAME_BY_ITEM_TYPE: Final[dict[str, str]] = {
    "web_search_call": "web_search",
    "file_search_call": "file_search",
    "code_interpreter_call": "code_interpreter",
    "image_generation_call": "image_generation",
}


def infer_builtin_tool_name(item_type: str | None) -> str | None:
    if not item_type:
        return None
    return BUILTIN_TOOL_NAME_BY_ITEM_TYPE.get(item_type)


__all__ = ["infer_builtin_tool_name", "BUILTIN_TOOL_NAME_BY_ITEM_TYPE"]
