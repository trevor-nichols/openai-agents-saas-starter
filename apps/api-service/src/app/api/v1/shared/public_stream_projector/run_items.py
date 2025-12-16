from __future__ import annotations

from typing import Literal, cast

from app.domain.ai.models import AgentStreamEvent

from ..streaming import (
    FunctionTool,
    McpTool,
    PublicSseEventBase,
    ToolOutputEvent,
    ToolStatusEvent,
    WebSearchTool,
)
from .builders import EventBuilder
from .sanitize import sanitize_json
from .scopes import tool_scope
from .state import ProjectionState, ToolState, ToolType
from .tooling import tool_name_from_run_item
from .utils import as_dict, coerce_str, extract_urls


def project_event(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if event.kind != "run_item_stream_event" or event.run_item_name not in {
        "tool_called",
        "tool_output",
        "mcp_approval_requested",
    }:
        return []

    payload = as_dict(event.payload) or {}
    raw_item = as_dict(payload.get("raw_item")) or payload
    raw_item_type = coerce_str((raw_item or {}).get("type")) or event.run_item_type
    tool_call_id = (
        coerce_str((raw_item or {}).get("call_id"))
        or coerce_str((raw_item or {}).get("id"))
        or event.tool_call_id
    )
    if not tool_call_id:
        return []

    inferred_name = tool_name_from_run_item(raw_item)
    raw_item_name = coerce_str((raw_item or {}).get("name"))
    tool_name = inferred_name or event.tool_name or raw_item_name or "unknown"

    tool_type: ToolType = "function"
    if event.run_item_name == "mcp_approval_requested" or raw_item_type == "mcp_call":
        tool_type = "mcp"
    else:
        builtin_tool: str | None = None
        if raw_item_type == "web_search_call":
            builtin_tool = "web_search"
        elif raw_item_type == "file_search_call":
            builtin_tool = "file_search"
        elif raw_item_type == "code_interpreter_call":
            builtin_tool = "code_interpreter"
        elif raw_item_type == "image_generation_call":
            builtin_tool = "image_generation"
        elif inferred_name in {"web_search", "file_search", "code_interpreter", "image_generation"}:
            builtin_tool = inferred_name

        if builtin_tool:
            tool_type = cast(ToolType, builtin_tool)

    tool_state = state.tool_state.setdefault(tool_call_id, ToolState(tool_type=tool_type))
    if tool_state.tool_type == "function" and tool_type != "function":
        tool_state.tool_type = tool_type
    tool_state.tool_name = tool_name
    scope = tool_scope(tool_call_id, state=state)

    if tool_type == "mcp":
        tool_state.server_label = (
            coerce_str((raw_item or {}).get("server_label"))
            or coerce_str((raw_item or {}).get("server"))
            or tool_state.server_label
        )

    if tool_type == "web_search":
        state.last_web_search_tool_call_id = tool_call_id
        action = as_dict((raw_item or {}).get("action"))
        query = coerce_str((action or {}).get("query"))
        if query:
            tool_state.query = query
        raw_status = coerce_str((raw_item or {}).get("status"))
        if raw_status in {"in_progress", "searching", "completed"}:
            tool_state.last_status = tool_state.last_status or raw_status

    if tool_type == "file_search":
        queries = (raw_item or {}).get("queries")
        if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
            tool_state.file_search_queries = [q for q in queries if q]

    out: list[PublicSseEventBase] = []

    if event.run_item_name == "mcp_approval_requested" and tool_type == "mcp":
        if tool_state.last_status != "awaiting_approval":
            tool_state.last_status = "awaiting_approval"
            if scope:
                item_id, output_index = scope
                out.append(
                    ToolStatusEvent(
                        **builder.item(
                            kind="tool.status",
                            item_id=item_id,
                            output_index=output_index,
                        ),
                        tool=McpTool(
                            tool_type="mcp",
                            tool_call_id=tool_call_id,
                            status="awaiting_approval",
                            tool_name=tool_name,
                            server_label=tool_state.server_label,
                        ),
                    )
                )

    if event.run_item_name == "tool_called" and tool_type == "function":
        if tool_state.last_status != "in_progress":
            tool_state.last_status = "in_progress"
            if scope:
                item_id, output_index = scope
                out.append(
                    ToolStatusEvent(
                        **builder.item(
                            kind="tool.status",
                            item_id=item_id,
                            output_index=output_index,
                        ),
                        tool=FunctionTool(
                            tool_type="function",
                            tool_call_id=tool_call_id,
                            status="in_progress",
                            name=tool_name,
                        ),
                    )
                )

    if event.run_item_name == "tool_called" and tool_type == "mcp":
        if tool_state.last_status != "in_progress":
            tool_state.last_status = "in_progress"
            if scope:
                item_id, output_index = scope
                out.append(
                    ToolStatusEvent(
                        **builder.item(
                            kind="tool.status",
                            item_id=item_id,
                            output_index=output_index,
                        ),
                        tool=McpTool(
                            tool_type="mcp",
                            tool_call_id=tool_call_id,
                            status="in_progress",
                            tool_name=tool_name,
                            server_label=tool_state.server_label,
                        ),
                    )
                )

    if event.run_item_name == "tool_output":
        output = payload.get("output")
        if output is None:
            output = payload.get("content")
        if output is None and isinstance(raw_item, dict):
            output = raw_item.get("output")
            if output is None:
                output = raw_item.get("content")

        if tool_type == "web_search" and output is not None:
            urls = [u for u in extract_urls(output) if u]
            if urls:
                prior = tool_state.sources or []
                merged_sources = [*prior, *[u for u in urls if u not in prior]]
                tool_state.sources = merged_sources

        if tool_type in {"function", "mcp"} and output is not None and scope:
            safe_output = AgentStreamEvent._strip_unserializable(output)
            sanitized_output, notices = sanitize_json(
                safe_output,
                path="output",
                max_string_chars=8_000,
            )
            item_id, output_index = scope
            out.append(
                ToolOutputEvent(
                    **builder.item(
                        kind="tool.output",
                        item_id=item_id,
                        output_index=output_index,
                        notices=notices or None,
                    ),
                    tool_call_id=tool_call_id,
                    tool_type=cast(Literal["function", "mcp"], tool_type),
                    output=sanitized_output,
                )
            )

        if tool_type == "function":
            tool_state.last_status = "completed"
            if scope:
                item_id, output_index = scope
                out.append(
                    ToolStatusEvent(
                        **builder.item(
                            kind="tool.status",
                            item_id=item_id,
                            output_index=output_index,
                        ),
                        tool=FunctionTool(
                            tool_type="function",
                            tool_call_id=tool_call_id,
                            status="completed",
                            name=tool_name,
                        ),
                    )
                )
        elif tool_type == "mcp":
            tool_state.last_status = "completed"
            if scope:
                item_id, output_index = scope
                out.append(
                    ToolStatusEvent(
                        **builder.item(
                            kind="tool.status",
                            item_id=item_id,
                            output_index=output_index,
                        ),
                        tool=McpTool(
                            tool_type="mcp",
                            tool_call_id=tool_call_id,
                            status="completed",
                            tool_name=tool_name,
                            server_label=tool_state.server_label,
                        ),
                    )
                )
        elif tool_type == "web_search":
            status: Literal["in_progress", "searching", "completed"] = "completed"
            if tool_state.last_status in {"in_progress", "searching", "completed"}:
                status = cast(
                    Literal["in_progress", "searching", "completed"],
                    tool_state.last_status,
                )
            if scope:
                item_id, output_index = scope
                out.append(
                    ToolStatusEvent(
                        **builder.item(
                            kind="tool.status",
                            item_id=item_id,
                            output_index=output_index,
                        ),
                        tool=WebSearchTool(
                            tool_type="web_search",
                            tool_call_id=tool_call_id,
                            status=status,
                            query=tool_state.query,
                            sources=tool_state.sources,
                        ),
                    )
                )

    return out
