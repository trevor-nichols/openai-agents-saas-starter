from __future__ import annotations

from app.domain.ai.models import AgentStreamEvent

from ...streaming import (
    OutputItemAddedEvent,
    OutputItemDoneEvent,
    PublicSseEventBase,
)
from ..builders import EventBuilder
from ..state import ProjectionState, ToolState, ToolType
from ..utils import as_dict, coerce_str


def project_output_items(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if event.kind != "raw_response_event" or event.raw_type not in {
        "response.output_item.added",
        "response.output_item.done",
    }:
        return []

    raw = as_dict(event.raw_event) or {}
    output_index = raw.get("output_index")
    output_item = as_dict(raw.get("item"))
    if not output_item or not isinstance(output_index, int):
        return []

    item_type = coerce_str(output_item.get("type"))
    item_id = coerce_str(output_item.get("id"))
    role = coerce_str(output_item.get("role"))
    status = coerce_str(output_item.get("status"))
    if not item_id or not item_type:
        return []

    out: list[PublicSseEventBase] = []
    if event.raw_type == "response.output_item.added":
        out.append(
            OutputItemAddedEvent(
                **builder.item(
                    kind="output_item.added",
                    item_id=item_id,
                    output_index=output_index,
                    provider_seq=event.sequence_number,
                ),
                item_type=item_type,
                role=role,
                status=status,
            )
        )
    else:
        out.append(
            OutputItemDoneEvent(
                **builder.item(
                    kind="output_item.done",
                    item_id=item_id,
                    output_index=output_index,
                    provider_seq=event.sequence_number,
                ),
                item_type=item_type,
                role=role,
                status=status,
            )
        )

    tool_type_from_item: ToolType | None = None
    if item_type == "web_search_call":
        tool_type_from_item = "web_search"
    elif item_type == "file_search_call":
        tool_type_from_item = "file_search"
    elif item_type == "code_interpreter_call":
        tool_type_from_item = "code_interpreter"
    elif item_type == "image_generation_call":
        tool_type_from_item = "image_generation"
    elif item_type in {"function_call", "custom_tool_call"}:
        tool_type_from_item = "function"
    elif item_type == "mcp_call":
        tool_type_from_item = "mcp"

    if tool_type_from_item:
        tool_state = state.tool_state.setdefault(item_id, ToolState(tool_type=tool_type_from_item))
        if tool_state.output_index is None:
            tool_state.output_index = output_index

        if item_type in {"function_call", "mcp_call", "custom_tool_call"}:
            tool_name = coerce_str(output_item.get("name") or output_item.get("tool_name"))
            if tool_name:
                tool_state.tool_name = tool_name
            if item_type == "mcp_call":
                server_label = coerce_str(
                    output_item.get("server_label") or output_item.get("server")
                )
                if server_label:
                    tool_state.server_label = server_label

    return out

