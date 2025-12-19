from __future__ import annotations

from app.domain.ai.models import AgentStreamEvent

from ...streaming import (
    CodeInterpreterTool,
    FileSearchTool,
    ImageGenerationTool,
    PublicSseEventBase,
    ToolStatusEvent,
    WebSearchTool,
)
from ..builders import EventBuilder
from ..scopes import tool_scope
from ..state import ProjectionState
from ..tooling import (
    as_code_interpreter_status,
    as_image_generation_status,
    as_search_status,
    merge_tool_call_into_state,
)
from ..utils import as_dict


def project_tool_call_updates(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    tool_call = as_dict(event.tool_call)
    if not tool_call:
        return []

    merged = merge_tool_call_into_state(state, tool_call)
    if (
        not merged
        or event.kind != "raw_response_event"
        or event.raw_type != "response.output_item.done"
    ):
        return []

    tool_call_id, tool_type, _status, notices = merged
    tool_state = state.tool_state.get(tool_call_id)
    if not tool_state:
        return []

    raw_event = as_dict(event.raw_event) or {}
    scope = tool_scope(tool_call_id, state=state, raw=raw_event)
    if scope is None:
        return []

    item_id, output_index = scope

    if tool_type == "file_search":
        file_search_status = as_search_status(tool_state.last_status)
        return [
            ToolStatusEvent(
                **builder.item(
                    kind="tool.status",
                    item_id=item_id,
                    output_index=output_index,
                    provider_seq=event.sequence_number,
                    notices=notices or None,
                ),
                tool=FileSearchTool(
                    tool_type="file_search",
                    tool_call_id=tool_call_id,
                    status=file_search_status,
                    queries=tool_state.file_search_queries,
                    results=tool_state.file_search_results,
                ),
            )
        ]

    if tool_type == "code_interpreter":
        code_interpreter_status = as_code_interpreter_status(tool_state.last_status)
        return [
            ToolStatusEvent(
                **builder.item(
                    kind="tool.status",
                    item_id=item_id,
                    output_index=output_index,
                    provider_seq=event.sequence_number,
                ),
                tool=CodeInterpreterTool(
                    tool_type="code_interpreter",
                    tool_call_id=tool_call_id,
                    status=code_interpreter_status,
                    container_id=tool_state.container_id,
                    container_mode=tool_state.container_mode,
                ),
            )
        ]

    if tool_type == "image_generation":
        image_generation_status = as_image_generation_status(tool_state.last_status)
        return [
            ToolStatusEvent(
                **builder.item(
                    kind="tool.status",
                    item_id=item_id,
                    output_index=output_index,
                    provider_seq=event.sequence_number,
                ),
                tool=ImageGenerationTool(
                    tool_type="image_generation",
                    tool_call_id=tool_call_id,
                    status=image_generation_status,
                    revised_prompt=tool_state.image_revised_prompt,
                    format=tool_state.image_format,
                    size=tool_state.image_size,
                    quality=tool_state.image_quality,
                    background=tool_state.image_background,
                    partial_image_index=tool_state.image_partial_image_index,
                ),
            )
        ]

    if tool_type == "web_search":
        web_search_status = as_search_status(tool_state.last_status or "completed")
        state.last_web_search_tool_call_id = tool_call_id
        return [
            ToolStatusEvent(
                **builder.item(
                    kind="tool.status",
                    item_id=item_id,
                    output_index=output_index,
                    provider_seq=event.sequence_number,
                ),
                tool=WebSearchTool(
                    tool_type="web_search",
                    tool_call_id=tool_call_id,
                    status=web_search_status,
                    query=tool_state.query,
                    sources=tool_state.sources,
                ),
            )
        ]

    return []

