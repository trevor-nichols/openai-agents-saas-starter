from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.api.v1.shared.streaming import (
    ContainerFileCitation,
    FileCitation,
    MessageAttachment,
    StreamingEvent,
    ToolCallPayload,
    UrlCitation,
)
from app.domain.ai.models import AgentStreamEvent


def _parse_annotations(raw: Any) -> list[UrlCitation | ContainerFileCitation | FileCitation] | None:
    if not isinstance(raw, list):
        return None

    parsed: list[UrlCitation | ContainerFileCitation | FileCitation] = []
    for ann in raw:
        if not isinstance(ann, dict):
            continue
        try:
            parsed.append(UrlCitation.model_validate(ann))
            continue
        except Exception:
            pass
        try:
            parsed.append(ContainerFileCitation.model_validate(ann))
            continue
        except Exception:
            pass
        try:
            parsed.append(FileCitation.model_validate(ann))
        except Exception:
            continue
    return parsed or None


def _parse_tool_call(raw: Any) -> ToolCallPayload | dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    try:
        return ToolCallPayload.model_validate(raw)
    except ValidationError:
        return raw


def _coerce_attachments(raw: Any) -> list[MessageAttachment | dict[str, Any]] | None:
    if raw is None:
        return None
    if not isinstance(raw, list):
        return None

    coerced: list[MessageAttachment | dict[str, Any]] = []
    for item in raw:
        if isinstance(item, MessageAttachment):
            coerced.append(item)
        elif isinstance(item, dict):
            coerced.append(item)
        else:
            continue
    return coerced or None


def normalize_stream_event(
    event: AgentStreamEvent,
    *,
    workflow_meta: dict[str, Any] | None = None,
    default_conversation_id: str | None = None,
    server_timestamp: str | None = None,
) -> StreamingEvent:
    """
    Normalize provider-specific AgentStreamEvent into the shared StreamingEvent DTO.

    - Never raises on unknown tool types; falls back to raw dict.
    - Best-effort parsing of citations and tool calls.
    """

    workflow_meta = workflow_meta or {}

    annotations = _parse_annotations(event.annotations) if event.annotations is not None else None
    parsed_tool_call = _parse_tool_call(event.tool_call)
    attachments = _coerce_attachments(event.attachments)

    return StreamingEvent(
        kind=event.kind,
        run_item_type=event.run_item_type,
        workflow_key=workflow_meta.get("workflow_key"),
        workflow_run_id=workflow_meta.get("workflow_run_id"),
        step_name=workflow_meta.get("step_name"),
        step_agent=workflow_meta.get("step_agent"),
        stage_name=workflow_meta.get("stage_name"),
        parallel_group=workflow_meta.get("parallel_group"),
        branch_index=workflow_meta.get("branch_index"),
        conversation_id=event.conversation_id or default_conversation_id,
        agent_used=event.agent,
        response_id=event.response_id,
        sequence_number=event.sequence_number,
        raw_type=event.raw_type,
        run_item_name=event.run_item_name,
        tool_call_id=event.tool_call_id,
        tool_name=event.tool_name,
        agent=event.agent,
        new_agent=event.new_agent,
        display_name=getattr(event, "display_name", None),
        text_delta=event.text_delta,
        reasoning_delta=event.reasoning_delta,
        response_text=event.response_text,
        structured_output=event.structured_output,
        is_terminal=event.is_terminal,
        event=getattr(event, "event", None),
        payload=event.payload if isinstance(event.payload, dict) else None,
        attachments=attachments,
        raw_event=event.raw_event if isinstance(event.raw_event, dict) else None,
        tool_call=parsed_tool_call,
        annotations=annotations,
        server_timestamp=server_timestamp,
    )


__all__ = ["normalize_stream_event"]
