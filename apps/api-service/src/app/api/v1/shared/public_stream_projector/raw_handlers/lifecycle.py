from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, cast

from app.domain.ai.models import AgentStreamEvent

from ...streaming import LifecycleEvent, PublicSseEventBase
from ..builders import EventBuilder
from ..state import ProjectionState
from ..utils import coerce_str


def project_lifecycle(
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


def project_service_lifecycle(
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

