from __future__ import annotations

from typing import cast

from app.domain.ai.models import AgentStreamEvent

from ..streaming import MessageAttachment, PublicSseEventBase
from .builders import EventBuilder
from .raw_handlers.citations import project_citations
from .raw_handlers.errors import project_terminal_errors
from .raw_handlers.lifecycle import project_lifecycle, project_service_lifecycle
from .raw_handlers.memory_checkpoint import project_memory_checkpoint
from .raw_handlers.messages import project_message_deltas
from .raw_handlers.output_items import project_output_items
from .raw_handlers.reasoning import project_reasoning_summary
from .raw_handlers.refusal import project_refusal
from .raw_handlers.tool_call_updates import project_tool_call_updates
from .raw_handlers.tools.arguments import project_tool_arguments
from .raw_handlers.tools.code_interpreter import project_code_interpreter_code
from .raw_handlers.tools.status import project_tool_status_raw
from .state import FinalStatus, ProjectionState


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

    terminal = project_terminal_errors(state, builder, event)
    if terminal:
        return terminal

    out.extend(project_tool_call_updates(state, builder, event))
    out.extend(project_lifecycle(state, builder, event))
    out.extend(project_service_lifecycle(state, builder, event))
    out.extend(project_memory_checkpoint(state, builder, event))
    out.extend(project_output_items(state, builder, event))
    out.extend(project_message_deltas(state, builder, event))
    out.extend(project_citations(state, builder, event))
    out.extend(project_reasoning_summary(state, builder, event))
    out.extend(project_refusal(state, builder, event))
    out.extend(project_tool_status_raw(state, builder, event, max_chunk_chars=max_chunk_chars))
    out.extend(project_code_interpreter_code(state, builder, event))
    out.extend(project_tool_arguments(state, builder, event))

    return out


def terminal_final_status(state: ProjectionState, event: AgentStreamEvent) -> FinalStatus:
    final_status: FinalStatus = "completed"
    if state.refusal_text:
        final_status = "refused"
    elif state.lifecycle_status in {"failed", "incomplete", "cancelled"}:
        final_status = cast(FinalStatus, state.lifecycle_status)
    elif event.response_text is None and event.structured_output is None:
        final_status = "incomplete"
    return final_status
