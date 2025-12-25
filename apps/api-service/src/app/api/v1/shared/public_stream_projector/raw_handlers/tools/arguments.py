from __future__ import annotations

import json
from typing import Any

from app.domain.ai.models import AgentStreamEvent

from ....streaming import (
    AgentTool,
    FunctionTool,
    PublicSseEventBase,
    StreamNotice,
    ToolArgumentsDeltaEvent,
    ToolArgumentsDoneEvent,
    ToolStatusEvent,
)
from ...builders import EventBuilder
from ...sanitize import sanitize_json, truncate_string
from ...scopes import tool_scope
from ...state import ProjectionState, ToolState
from ...tooling import args_tool_type_from_raw_type, set_output_index_if_missing
from ...utils import (
    agent_tool_name_map_from_meta,
    agent_tool_names_from_meta,
    as_dict,
    coerce_str,
    safe_json_parse,
)


def project_tool_arguments(
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

    if event.raw_type in {
        "response.function_call_arguments.delta",
        "response.custom_tool_call_input.delta",
        "response.mcp_call_arguments.delta",
    }:
        arguments_delta = raw.get("delta")
        if isinstance(arguments_delta, str) and arguments_delta:
            tool_type = args_tool_type_from_raw_type(event.raw_type)
            tool_state = state.tool_state.setdefault(tool_call_id, ToolState(tool_type=tool_type))
            tool_name = coerce_str(raw.get("name")) or tool_state.tool_name
            if tool_type == "function":
                agent_tool_names = agent_tool_names_from_meta(event.metadata)
                if tool_name and tool_name in agent_tool_names:
                    tool_type = "agent"
            if tool_type != tool_state.tool_type:
                tool_state.tool_type = tool_type
            tool_state.arguments_text += arguments_delta
        return []

    if event.raw_type not in {
        "response.function_call_arguments.done",
        "response.custom_tool_call_input.done",
        "response.mcp_call_arguments.done",
    }:
        return []

    tool_type = args_tool_type_from_raw_type(event.raw_type)
    tool_state = state.tool_state.setdefault(tool_call_id, ToolState(tool_type=tool_type))

    if event.raw_type == "response.custom_tool_call_input.done":
        arguments_text = raw.get("input")
        tool_name = tool_state.tool_name or "unknown"
    else:
        arguments_text = raw.get("arguments")
        tool_name = coerce_str(raw.get("name")) or tool_state.tool_name or "unknown"

    if tool_type == "function":
        agent_tool_names = agent_tool_names_from_meta(event.metadata)
        if tool_name in agent_tool_names:
            tool_type = "agent"
    if tool_state.tool_type == "function" and tool_type == "agent":
        tool_state.tool_type = "agent"

    if tool_type == "agent" and tool_state.agent_name is None:
        agent_tool_name_map = agent_tool_name_map_from_meta(event.metadata)
        tool_state.agent_name = agent_tool_name_map.get(tool_name) or tool_state.agent_name

    if not isinstance(arguments_text, str):
        return []

    set_output_index_if_missing(tool_state, raw)
    scope = tool_scope(tool_call_id, state=state)
    if not scope:
        # Can't emit item-scoped tool argument events without an output_index.
        tool_state.arguments_text = arguments_text
        tool_state.tool_name = tool_name
        tool_state.last_status = tool_state.last_status or "in_progress"
        return []

    item_id, output_index = scope

    parsed_json = safe_json_parse(arguments_text)
    notices: list[StreamNotice] = []
    sanitized_json: dict[str, Any] | None = None
    sanitized_text = arguments_text
    if parsed_json is not None:
        sanitized_any, notices = sanitize_json(
            parsed_json,
            path="arguments_json",
            max_string_chars=4_000,
        )
        sanitized_json = sanitized_any if isinstance(sanitized_any, dict) else None
        if sanitized_json is not None:
            sanitized_text = json.dumps(sanitized_json, ensure_ascii=False)

    sanitized_text, truncated_notice = truncate_string(
        value=sanitized_text,
        path="arguments_text",
        max_chars=8_000,
    )
    if truncated_notice:
        notices.append(truncated_notice)

    tool_state.arguments_text = sanitized_text
    tool_state.tool_name = tool_name
    previously_emitted_status = tool_state.last_status is not None
    tool_state.last_status = tool_state.last_status or "in_progress"

    out: list[PublicSseEventBase] = []
    if not previously_emitted_status and tool_state.last_status == "in_progress":
        if tool_type == "function":
            out.append(
                ToolStatusEvent(
                    **builder.item(
                        kind="tool.status",
                        item_id=item_id,
                        output_index=output_index,
                        provider_seq=event.sequence_number,
                    ),
                    tool=FunctionTool(
                        tool_type="function",
                        tool_call_id=tool_call_id,
                        status="in_progress",
                        name=tool_name,
                    ),
                )
            )
        elif tool_type == "agent":
            out.append(
                ToolStatusEvent(
                    **builder.item(
                        kind="tool.status",
                        item_id=item_id,
                        output_index=output_index,
                        provider_seq=event.sequence_number,
                    ),
                    tool=AgentTool(
                        tool_type="agent",
                        tool_call_id=tool_call_id,
                        status="in_progress",
                        name=tool_name,
                    ),
                )
            )

    if sanitized_text:
        chunk_size = 2_000
        idx = 0
        while idx < len(sanitized_text):
            out.append(
                ToolArgumentsDeltaEvent(
                    **builder.item(
                        kind="tool.arguments.delta",
                        item_id=item_id,
                        output_index=output_index,
                        provider_seq=event.sequence_number,
                    ),
                    tool_call_id=tool_call_id,
                    tool_type=tool_type,
                    tool_name=tool_name,
                    delta=sanitized_text[idx : idx + chunk_size],
                )
            )
            idx += chunk_size

    out.append(
        ToolArgumentsDoneEvent(
            **builder.item(
                kind="tool.arguments.done",
                item_id=item_id,
                output_index=output_index,
                provider_seq=event.sequence_number,
                notices=notices or None,
            ),
            tool_call_id=tool_call_id,
            tool_type=tool_type,
            tool_name=tool_name,
            arguments_text=sanitized_text,
            arguments_json=sanitized_json,
        )
    )

    return out
