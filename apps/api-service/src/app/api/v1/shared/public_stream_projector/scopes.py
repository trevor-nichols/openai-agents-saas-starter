from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .state import ProjectionState
from .utils import coerce_str


def item_scope_from_raw(
    raw: Mapping[str, Any] | None, *, id_key: str = "item_id"
) -> tuple[str, int] | None:
    if not raw:
        return None
    item_id = coerce_str(raw.get(id_key))
    output_index = raw.get("output_index")
    if not item_id or not isinstance(output_index, int):
        return None
    return item_id, output_index


def tool_scope(
    tool_call_id: str, *, state: ProjectionState, raw: Mapping[str, Any] | None = None
) -> tuple[str, int] | None:
    output_index: int | None = None
    if raw is not None:
        raw_index = raw.get("output_index")
        if isinstance(raw_index, int):
            output_index = raw_index

    tool_state = state.tool_state.get(tool_call_id)
    if tool_state is not None:
        if tool_state.output_index is not None:
            output_index = tool_state.output_index
        elif output_index is not None:
            tool_state.output_index = output_index

    if output_index is None:
        return None
    return tool_call_id, output_index

