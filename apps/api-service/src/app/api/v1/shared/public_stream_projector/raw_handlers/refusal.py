from __future__ import annotations

from app.domain.ai.models import AgentStreamEvent

from ...streaming import PublicSseEventBase, RefusalDeltaEvent, RefusalDoneEvent
from ..builders import EventBuilder
from ..scopes import item_scope_from_raw
from ..state import ProjectionState
from ..utils import as_dict


def project_refusal(
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

