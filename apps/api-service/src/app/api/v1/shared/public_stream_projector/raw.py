from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Literal, cast

from app.domain.ai.models import AgentStreamEvent

from ..streaming import (
    ChunkDeltaEvent,
    ChunkDoneEvent,
    ChunkTarget,
    CodeInterpreterTool,
    ContainerFileCitation,
    ErrorEvent,
    ErrorPayload,
    FileCitation,
    FileSearchTool,
    FunctionTool,
    ImageGenerationTool,
    LifecycleEvent,
    McpTool,
    MessageAttachment,
    MessageCitationEvent,
    MessageDeltaEvent,
    OutputItemAddedEvent,
    OutputItemDoneEvent,
    PublicCitation,
    PublicSseEventBase,
    ReasoningSummaryDeltaEvent,
    RefusalDeltaEvent,
    RefusalDoneEvent,
    StreamNotice,
    ToolArgumentsDeltaEvent,
    ToolArgumentsDoneEvent,
    ToolCodeDeltaEvent,
    ToolCodeDoneEvent,
    ToolStatusEvent,
    UrlCitation,
    WebSearchTool,
)
from .builders import EventBuilder
from .sanitize import sanitize_json, truncate_string
from .scopes import item_scope_from_raw, tool_scope
from .state import FinalStatus, ProjectionState, ToolState, ToolType
from .tooling import (
    args_tool_type_from_raw_type,
    as_code_interpreter_status,
    as_image_generation_status,
    as_search_status,
    merge_tool_call_into_state,
)
from .utils import as_dict, coerce_str, safe_json_parse


def apply_attachments(state: ProjectionState, event: AgentStreamEvent) -> None:
    if not isinstance(event.attachments, list):
        return
    for item in event.attachments:
        if not isinstance(item, dict):
            continue
        try:
            attachment = MessageAttachment.model_validate(item)
        except Exception:
            continue
        if attachment.object_id in state.seen_attachment_ids:
            continue
        state.seen_attachment_ids.add(attachment.object_id)
        state.attachments.append(attachment)


def project_event(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
    *,
    max_chunk_chars: int,
) -> list[PublicSseEventBase]:
    """Project non-run-item AgentStreamEvent records into public SSE events."""

    out: list[PublicSseEventBase] = []

    terminal = _project_terminal_errors(state, builder, event)
    if terminal:
        return terminal

    out.extend(_project_tool_call_updates(state, builder, event))
    out.extend(_project_lifecycle(state, builder, event))
    out.extend(_project_service_lifecycle(state, builder, event))
    out.extend(_project_output_items(state, builder, event))
    out.extend(_project_message_deltas(state, builder, event))
    out.extend(_project_citations(state, builder, event))
    out.extend(_project_reasoning_summary(state, builder, event))
    out.extend(_project_refusal(state, builder, event))
    out.extend(_project_tool_status_raw(state, builder, event, max_chunk_chars=max_chunk_chars))
    out.extend(_project_code_interpreter_code(state, builder, event))
    out.extend(_project_tool_arguments(state, builder, event))

    return out


def _project_terminal_errors(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if event.kind == "raw_response_event" and event.raw_type == "error":
        raw = as_dict(event.raw_event) or {}
        code = coerce_str(raw.get("code"))
        message = coerce_str(raw.get("message")) or "Provider error"
        state.terminal_emitted = True
        return [
            ErrorEvent(
                **builder.base(kind="error", provider_seq=event.sequence_number),
                error=ErrorPayload(
                    code=code,
                    message=message,
                    source="provider",
                    is_retryable=False,
                ),
            )
        ]

    if event.kind == "error":
        payload = as_dict(event.payload) or {}
        message = (
            coerce_str(payload.get("message"))
            or coerce_str(payload.get("error"))
            or "Server error"
        )
        state.terminal_emitted = True
        return [
            ErrorEvent(
                **builder.base(kind="error"),
                error=ErrorPayload(
                    code=None,
                    message=message,
                    source="server",
                    is_retryable=False,
                ),
            )
        ]

    return []


def _project_tool_call_updates(
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


def _project_lifecycle(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if event.kind != "raw_response_event" or not isinstance(event.raw_type, str):
        return []
    if not event.raw_type.startswith("response."):
        return []

    lifecycle_map = {
        "response.created": "in_progress",
        "response.in_progress": "in_progress",
        "response.queued": "queued",
        "response.completed": "completed",
        "response.failed": "failed",
        "response.incomplete": "incomplete",
    }
    lifecycle = lifecycle_map.get(event.raw_type)
    if not lifecycle:
        return []

    state.lifecycle_status = cast(
        Literal["queued", "in_progress", "completed", "failed", "incomplete"],
        lifecycle,
    )
    return [
        LifecycleEvent(
            **builder.base(kind="lifecycle", provider_seq=event.sequence_number),
            status=state.lifecycle_status,
        )
    ]


def _project_service_lifecycle(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if event.kind != "lifecycle":
        return []
    meta = event.metadata if isinstance(event.metadata, Mapping) else {}
    run_state = coerce_str(meta.get("state"))
    if run_state not in {"cancelled", "canceled"}:
        return []

    state.lifecycle_status = "cancelled"
    return [
        LifecycleEvent(
            **builder.base(kind="lifecycle"),
            status="cancelled",
            reason=coerce_str(meta.get("reason")),
        )
    ]


def _project_output_items(
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


def _project_message_deltas(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if (
        event.kind != "raw_response_event"
        or event.raw_type != "response.output_text.delta"
        or event.text_delta is None
    ):
        return []

    raw = as_dict(event.raw_event) or {}
    scope = item_scope_from_raw(raw)
    content_index = raw.get("content_index")
    if not scope or not isinstance(content_index, int):
        return []
    item_id, output_index = scope
    return [
        MessageDeltaEvent(
            **builder.item(
                kind="message.delta",
                item_id=item_id,
                output_index=output_index,
                provider_seq=event.sequence_number,
            ),
            content_index=content_index,
            delta=event.text_delta,
        )
    ]


def _project_citations(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if (
        event.kind != "raw_response_event"
        or event.raw_type != "response.output_text.annotation.added"
    ):
        return []

    raw = as_dict(event.raw_event) or {}
    scope = item_scope_from_raw(raw)
    raw_content_index = raw.get("content_index")
    content_index = raw_content_index if isinstance(raw_content_index, int) else None
    if scope and content_index is not None:
        message_item_id, message_output_index = scope
    else:
        message_item_id = None
        message_output_index = None

    out: list[PublicSseEventBase] = []
    for ann in event.annotations or []:
        citation_type = ann.get("type")
        if citation_type == "url_citation":
            citation: PublicCitation = UrlCitation.model_validate(ann)
            if isinstance(citation, UrlCitation) and state.last_web_search_tool_call_id:
                tool_call_id = state.last_web_search_tool_call_id
                web_state = state.tool_state.setdefault(
                    tool_call_id,
                    ToolState(tool_type="web_search"),
                )
                sources = web_state.sources or []
                if citation.url not in sources:
                    web_state.sources = [*sources, citation.url]
                    # Citations can arrive after the tool status is already marked completed.
                    # Emit an updated tool.status so the UI can display gathered sources.
                    tool_item_scope = tool_scope(tool_call_id, state=state)
                    if tool_item_scope:
                        tool_item_id, tool_output_index = tool_item_scope
                        out.append(
                            ToolStatusEvent(
                                **builder.item(
                                    kind="tool.status",
                                    item_id=tool_item_id,
                                    output_index=tool_output_index,
                                    provider_seq=event.sequence_number,
                                ),
                                tool=WebSearchTool(
                                    tool_type="web_search",
                                    tool_call_id=tool_call_id,
                                    status=as_search_status(web_state.last_status or "completed"),
                                    query=web_state.query,
                                    sources=web_state.sources,
                                ),
                            )
                        )
        elif citation_type == "container_file_citation":
            citation = ContainerFileCitation.model_validate(ann)
        else:
            citation = FileCitation.model_validate(ann)

        if (
            message_item_id is not None
            and message_output_index is not None
            and content_index is not None
        ):
            out.append(
                MessageCitationEvent(
                    **builder.item(
                        kind="message.citation",
                        item_id=message_item_id,
                        output_index=message_output_index,
                        provider_seq=event.sequence_number,
                    ),
                    content_index=content_index,
                    citation=citation,
                )
            )

    return out


def _project_reasoning_summary(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if event.kind != "raw_response_event" or not isinstance(event.raw_type, str):
        return []

    out: list[PublicSseEventBase] = []

    if event.raw_type == "response.reasoning_summary_text.delta":
        raw = as_dict(event.raw_event) or {}
        scope = item_scope_from_raw(raw)
        summary_index = raw.get("summary_index")
        delta = event.reasoning_delta or ""
        if delta and scope and isinstance(summary_index, int):
            state.reasoning_summary_text += delta
            item_id, output_index = scope
            out.append(
                ReasoningSummaryDeltaEvent(
                    **builder.item(
                        kind="reasoning_summary.delta",
                        item_id=item_id,
                        output_index=output_index,
                        provider_seq=event.sequence_number,
                    ),
                    summary_index=summary_index,
                    delta=delta,
                )
            )
        return out

    if event.raw_type == "response.reasoning_summary_text.done":
        raw = as_dict(event.raw_event) or {}
        scope = item_scope_from_raw(raw)
        summary_index = raw.get("summary_index")
        text = raw.get("text")
        if isinstance(text, str) and text and scope and isinstance(summary_index, int):
            item_id, output_index = scope
            if not state.reasoning_summary_text:
                state.reasoning_summary_text = text
                out.append(
                    ReasoningSummaryDeltaEvent(
                        **builder.item(
                            kind="reasoning_summary.delta",
                            item_id=item_id,
                            output_index=output_index,
                            provider_seq=event.sequence_number,
                        ),
                        summary_index=summary_index,
                        delta=text,
                    )
                )
            elif text.startswith(state.reasoning_summary_text):
                suffix = text[len(state.reasoning_summary_text) :]
                if suffix:
                    state.reasoning_summary_text = text
                    out.append(
                        ReasoningSummaryDeltaEvent(
                            **builder.item(
                                kind="reasoning_summary.delta",
                                item_id=item_id,
                                output_index=output_index,
                                provider_seq=event.sequence_number,
                            ),
                            summary_index=summary_index,
                            delta=suffix,
                        )
                    )
        return out

    return []


def _project_refusal(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if event.kind != "raw_response_event" or not isinstance(event.raw_type, str):
        return []

    raw = as_dict(event.raw_event) or {}
    scope = item_scope_from_raw(raw)
    content_index = raw.get("content_index")
    if not scope or not isinstance(content_index, int):
        return []
    item_id, output_index = scope

    if event.raw_type == "response.refusal.delta":
        refusal_delta = raw.get("delta")
        if isinstance(refusal_delta, str) and refusal_delta:
            state.refusal_text += refusal_delta
            return [
                RefusalDeltaEvent(
                    **builder.item(
                        kind="refusal.delta",
                        item_id=item_id,
                        output_index=output_index,
                        provider_seq=event.sequence_number,
                    ),
                    content_index=content_index,
                    delta=refusal_delta,
                )
            ]
        return []

    if event.raw_type == "response.refusal.done":
        refusal_text = raw.get("refusal")
        if isinstance(refusal_text, str) and refusal_text:
            state.refusal_text = refusal_text
            return [
                RefusalDoneEvent(
                    **builder.item(
                        kind="refusal.done",
                        item_id=item_id,
                        output_index=output_index,
                        provider_seq=event.sequence_number,
                    ),
                    content_index=content_index,
                    refusal_text=refusal_text,
                )
            ]
        return []

    return []


def _project_tool_status_raw(
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
        raw_output_index = raw.get("output_index")
        if isinstance(raw_output_index, int) and tool_state.output_index is None:
            tool_state.output_index = raw_output_index
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
        raw_output_index = raw.get("output_index")
        if isinstance(raw_output_index, int) and tool_state.output_index is None:
            tool_state.output_index = raw_output_index
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
        raw_output_index = raw.get("output_index")
        if isinstance(raw_output_index, int) and tool_state.output_index is None:
            tool_state.output_index = raw_output_index
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
        raw_output_index = raw.get("output_index")
        if isinstance(raw_output_index, int) and tool_state.output_index is None:
            tool_state.output_index = raw_output_index

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
                _chunk_base64(
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
        raw_output_index = raw.get("output_index")
        if isinstance(raw_output_index, int) and tool_state.output_index is None:
            tool_state.output_index = raw_output_index
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


def _project_code_interpreter_code(
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
        raw_output_index = raw.get("output_index")
        if isinstance(raw_output_index, int) and tool_state.output_index is None:
            tool_state.output_index = raw_output_index
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
        raw_output_index = raw.get("output_index")
        if isinstance(raw_output_index, int) and tool_state.output_index is None:
            tool_state.output_index = raw_output_index
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


def _project_tool_arguments(
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

    if not isinstance(arguments_text, str):
        return []

    raw_output_index = raw.get("output_index")
    if isinstance(raw_output_index, int) and tool_state.output_index is None:
        tool_state.output_index = raw_output_index
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
    if (
        tool_type == "function"
        and not previously_emitted_status
        and tool_state.last_status == "in_progress"
    ):
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


def _chunk_base64(
    *,
    builder: EventBuilder,
    item_id: str,
    output_index: int,
    provider_seq: int | None,
    target: ChunkTarget,
    b64: str,
    max_chunk_chars: int,
) -> list[PublicSseEventBase]:
    chunks: list[PublicSseEventBase] = []
    idx = 0
    chunk_index = 0
    while idx < len(b64):
        part = b64[idx : idx + max_chunk_chars]
        chunks.append(
            ChunkDeltaEvent(
                **builder.item(
                    kind="chunk.delta",
                    item_id=item_id,
                    output_index=output_index,
                    provider_seq=provider_seq,
                ),
                target=target,
                encoding="base64",
                chunk_index=chunk_index,
                data=part,
            )
        )
        idx += max_chunk_chars
        chunk_index += 1
    chunks.append(
        ChunkDoneEvent(
            **builder.item(
                kind="chunk.done",
                item_id=item_id,
                output_index=output_index,
                provider_seq=provider_seq,
            ),
            target=target,
        )
    )
    return chunks


def terminal_final_status(state: ProjectionState, event: AgentStreamEvent) -> FinalStatus:
    final_status: FinalStatus = "completed"
    if state.refusal_text:
        final_status = "refused"
    elif state.lifecycle_status in {"failed", "incomplete", "cancelled"}:
        final_status = cast(FinalStatus, state.lifecycle_status)
    elif event.response_text is None and event.structured_output is None:
        final_status = "incomplete"
    return final_status
