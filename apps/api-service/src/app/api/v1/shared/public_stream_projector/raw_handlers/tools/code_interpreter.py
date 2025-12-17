from __future__ import annotations

from app.domain.ai.models import AgentStreamEvent

from ....streaming import (
    PublicSseEventBase,
    ToolCodeDeltaEvent,
    ToolCodeDoneEvent,
)
from ...builders import EventBuilder
from ...scopes import tool_scope
from ...state import ProjectionState, ToolState
from ...tooling import set_output_index_if_missing
from ...utils import as_dict, coerce_str


def project_code_interpreter_code(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if event.kind != "raw_response_event" or not isinstance(event.raw_type, str):
        return []

    raw = as_dict(event.raw_event) or {}
    tool_call_id = coerce_str(raw.get("item_id"))
    if not tool_call_id:
        return []

    if event.raw_type == "response.code_interpreter_call_code.delta":
        code_delta = raw.get("delta")
        if not isinstance(code_delta, str) or not code_delta:
            return []
        tool_state = state.tool_state.setdefault(
            tool_call_id, ToolState(tool_type="code_interpreter")
        )
        set_output_index_if_missing(tool_state, raw)
        scope = tool_scope(tool_call_id, state=state)
        if not scope:
            return []
        item_id, output_index = scope
        return [
            ToolCodeDeltaEvent(
                **builder.item(
                    kind="tool.code.delta",
                    item_id=item_id,
                    output_index=output_index,
                    provider_seq=event.sequence_number,
                ),
                tool_call_id=tool_call_id,
                delta=code_delta,
            )
        ]

    if event.raw_type == "response.code_interpreter_call_code.done":
        code = raw.get("code")
        if not isinstance(code, str):
            return []
        tool_state = state.tool_state.setdefault(
            tool_call_id, ToolState(tool_type="code_interpreter")
        )
        set_output_index_if_missing(tool_state, raw)
        scope = tool_scope(tool_call_id, state=state)
        if not scope:
            return []
        item_id, output_index = scope
        return [
            ToolCodeDoneEvent(
                **builder.item(
                    kind="tool.code.done",
                    item_id=item_id,
                    output_index=output_index,
                    provider_seq=event.sequence_number,
                ),
                tool_call_id=tool_call_id,
                code=code,
            )
        ]

    return []

