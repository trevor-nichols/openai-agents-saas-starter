from __future__ import annotations

from app.domain.ai.models import AgentStreamEvent

from ...streaming import MessageDeltaEvent, PublicSseEventBase
from ..builders import EventBuilder
from ..scopes import item_scope_from_raw
from ..state import ProjectionState
from ..utils import as_dict


def project_message_deltas(
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

