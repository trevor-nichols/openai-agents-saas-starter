from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, cast

from app.domain.ai.models import AgentStreamEvent

from ...streaming import MemoryCheckpointEvent, MemoryCheckpointPayload, PublicSseEventBase
from ..builders import EventBuilder
from ..state import ProjectionState
from ..utils import coerce_str


def _coerce_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except Exception:
        return None


def _coerce_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _coerce_str_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    out: list[str] = []
    for item in value:
        s = coerce_str(item)
        if s:
            out.append(s)
    return out


def project_memory_checkpoint(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if event.kind != "lifecycle" or event.event != "memory_compaction":
        return []

    payload = event.payload if isinstance(event.payload, Mapping) else {}
    strategy = coerce_str(payload.get("strategy")) or "compact"
    if strategy not in {"compact", "summarize", "trim"}:
        strategy = "compact"

    checkpoint = MemoryCheckpointPayload(
        strategy=cast(Literal["compact", "summarize", "trim"], strategy),
        trigger_reason=coerce_str(payload.get("trigger_reason")),
        tokens_before=_coerce_int(payload.get("tokens_before")),
        tokens_after=_coerce_int(payload.get("tokens_after")),
        compacted_count=_coerce_int(payload.get("compacted_count")),
        compacted_inputs=_coerce_int(payload.get("compacted_inputs")),
        compacted_outputs=_coerce_int(payload.get("compacted_outputs")),
        keep_turns=_coerce_int(payload.get("keep_turns")),
        trigger_turns=_coerce_int(payload.get("trigger_turns")),
        clear_tool_inputs=_coerce_bool(payload.get("clear_tool_inputs")),
        excluded_tools=_coerce_str_list(payload.get("excluded_tools")),
        included_tools=_coerce_str_list(payload.get("included_tools")),
        total_items_before=_coerce_int(payload.get("total_items_before")),
        total_items_after=_coerce_int(payload.get("total_items_after")),
        turns_before=_coerce_int(payload.get("turns_before")),
        turns_after=_coerce_int(payload.get("turns_after")),
    )
    return [
        MemoryCheckpointEvent(
            **builder.base(kind="memory.checkpoint"),
            checkpoint=checkpoint,
        )
    ]

