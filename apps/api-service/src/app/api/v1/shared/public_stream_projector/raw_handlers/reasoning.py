from __future__ import annotations

from app.domain.ai.models import AgentStreamEvent

from ...streaming import (
    PublicSseEventBase,
    ReasoningSummaryDeltaEvent,
    ReasoningSummaryPartAddedEvent,
    ReasoningSummaryPartDoneEvent,
)
from ..builders import EventBuilder
from ..scopes import item_scope_from_raw
from ..state import ProjectionState
from ..utils import as_dict, coerce_str


def project_reasoning_summary(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if event.kind != "raw_response_event" or not isinstance(event.raw_type, str):
        return []

    out: list[PublicSseEventBase] = []

    if event.raw_type in {
        "response.reasoning_summary_part.added",
        "response.reasoning_summary_part.done",
    }:
        raw = as_dict(event.raw_event) or {}
        scope = item_scope_from_raw(raw)
        summary_index = raw.get("summary_index")
        part = as_dict(raw.get("part")) or {}
        part_type = coerce_str(part.get("type"))
        part_text = part.get("text")
        if (
            scope
            and isinstance(summary_index, int)
            and part_type == "summary_text"
            and isinstance(part_text, str)
        ):
            item_id, output_index = scope
            if event.raw_type == "response.reasoning_summary_part.added":
                out.append(
                    ReasoningSummaryPartAddedEvent(
                        **builder.item(
                            kind="reasoning_summary.part.added",
                            item_id=item_id,
                            output_index=output_index,
                            provider_seq=event.sequence_number,
                        ),
                        summary_index=summary_index,
                        text=part_text,
                    )
                )
            elif part_text:
                out.append(
                    ReasoningSummaryPartDoneEvent(
                        **builder.item(
                            kind="reasoning_summary.part.done",
                            item_id=item_id,
                            output_index=output_index,
                            provider_seq=event.sequence_number,
                        ),
                        summary_index=summary_index,
                        text=part_text,
                    )
                )
        return out

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

