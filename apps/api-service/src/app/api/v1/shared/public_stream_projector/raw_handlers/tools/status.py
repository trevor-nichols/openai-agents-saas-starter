from __future__ import annotations

from typing import Literal, cast

from app.domain.ai.models import AgentStreamEvent

from ....streaming import (
    ChunkTarget,
    CodeInterpreterTool,
    FileSearchTool,
    ImageGenerationTool,
    McpTool,
    PublicSseEventBase,
    ToolStatusEvent,
    WebSearchTool,
)
from ...builders import EventBuilder
from ...scopes import tool_scope
from ...state import ProjectionState, ToolState
from ...tooling import (
    as_code_interpreter_status,
    as_image_generation_status,
    as_search_status,
    set_output_index_if_missing,
)
from ...utils import as_dict, coerce_str
from .chunking import chunk_base64


def project_tool_status_raw(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
    *,
    max_chunk_chars: int,
) -> list[PublicSseEventBase]:
    if event.kind != "raw_response_event" or not isinstance(event.raw_type, str):
        return []

    raw = as_dict(event.raw_event) or {}
    tool_call_id = coerce_str(raw.get("item_id"))
    if not tool_call_id:
        return []

    scope = tool_scope(tool_call_id, state=state, raw=raw)
    out: list[PublicSseEventBase] = []

    if event.raw_type.startswith("response.web_search_call."):
        status_fragment = event.raw_type.rsplit(".", 1)[-1]
        web_search_status = as_search_status(status_fragment)
        tool_state = state.tool_state.setdefault(tool_call_id, ToolState(tool_type="web_search"))
        tool_state.tool_type = "web_search"
        tool_state.last_status = web_search_status
        set_output_index_if_missing(tool_state, raw)
        state.last_web_search_tool_call_id = tool_call_id
        if scope:
            item_id, output_index = scope
            out.append(
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
            )
        return out

    if event.raw_type.startswith("response.file_search_call."):
        status_fragment = event.raw_type.rsplit(".", 1)[-1]
        file_search_status = as_search_status(status_fragment)
        tool_state = state.tool_state.setdefault(tool_call_id, ToolState(tool_type="file_search"))
        tool_state.tool_type = "file_search"
        tool_state.last_status = file_search_status
        set_output_index_if_missing(tool_state, raw)
        if scope:
            item_id, output_index = scope
            out.append(
                ToolStatusEvent(
                    **builder.item(
                        kind="tool.status",
                        item_id=item_id,
                        output_index=output_index,
                        provider_seq=event.sequence_number,
                    ),
                    tool=FileSearchTool(
                        tool_type="file_search",
                        tool_call_id=tool_call_id,
                        status=file_search_status,
                        queries=tool_state.file_search_queries,
                        results=tool_state.file_search_results,
                    ),
                )
            )
        return out

    if event.raw_type.startswith("response.code_interpreter_call."):
        status_fragment = event.raw_type.rsplit(".", 1)[-1]
        code_interpreter_status = as_code_interpreter_status(status_fragment)
        tool_state = state.tool_state.setdefault(
            tool_call_id, ToolState(tool_type="code_interpreter")
        )
        tool_state.tool_type = "code_interpreter"
        tool_state.last_status = code_interpreter_status
        set_output_index_if_missing(tool_state, raw)
        if scope:
            item_id, output_index = scope
            out.append(
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
            )
        return out

    if event.raw_type.startswith("response.image_generation_call."):
        status_fragment = event.raw_type.rsplit(".", 1)[-1]
        image_generation_status = as_image_generation_status(status_fragment)
        tool_state = state.tool_state.setdefault(
            tool_call_id, ToolState(tool_type="image_generation")
        )
        tool_state.tool_type = "image_generation"
        tool_state.last_status = image_generation_status
        set_output_index_if_missing(tool_state, raw)

        partial_image_index = raw.get("partial_image_index")
        if not isinstance(partial_image_index, int):
            partial_image_index = None
        tool_state.image_partial_image_index = partial_image_index

        if scope:
            item_id, output_index = scope
            out.append(
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
                        revised_prompt=tool_state.image_revised_prompt
                        or coerce_str(raw.get("revised_prompt")),
                        format=tool_state.image_format
                        or coerce_str(raw.get("format") or raw.get("output_format")),
                        size=tool_state.image_size or coerce_str(raw.get("size")),
                        quality=tool_state.image_quality or coerce_str(raw.get("quality")),
                        background=tool_state.image_background
                        or coerce_str(raw.get("background")),
                        partial_image_index=partial_image_index,
                    ),
                )
            )

        partial_b64 = raw.get("partial_image_b64") or raw.get("b64_json")
        if (
            image_generation_status == "partial_image"
            and isinstance(partial_b64, str)
            and partial_b64
            and scope
        ):
            item_id, output_index = scope
            out.extend(
                chunk_base64(
                    builder=builder,
                    item_id=item_id,
                    output_index=output_index,
                    provider_seq=event.sequence_number,
                    target=ChunkTarget(
                        entity_kind="tool_call",
                        entity_id=tool_call_id,
                        field="partial_image_b64",
                        part_index=partial_image_index,
                    ),
                    b64=partial_b64,
                    max_chunk_chars=max_chunk_chars,
                )
            )
        return out

    if event.raw_type.startswith("response.mcp_call."):
        status_fragment = event.raw_type.rsplit(".", 1)[-1]
        mcp_status: Literal["in_progress", "completed", "failed"] = "in_progress"
        if status_fragment in {"in_progress", "completed", "failed"}:
            mcp_status = cast(Literal["in_progress", "completed", "failed"], status_fragment)
        tool_state = state.tool_state.setdefault(tool_call_id, ToolState(tool_type="mcp"))
        tool_state.last_status = mcp_status
        set_output_index_if_missing(tool_state, raw)
        if scope:
            item_id, output_index = scope
            out.append(
                ToolStatusEvent(
                    **builder.item(
                        kind="tool.status",
                        item_id=item_id,
                        output_index=output_index,
                        provider_seq=event.sequence_number,
                    ),
                    tool=McpTool(
                        tool_type="mcp",
                        tool_call_id=tool_call_id,
                        status=mcp_status,
                        tool_name=tool_state.tool_name or "unknown",
                        server_label=tool_state.server_label,
                    ),
                )
            )
        return out

    return []

