from __future__ import annotations

from app.domain.ai.models import AgentStreamEvent

from ...streaming import ErrorEvent, ErrorPayload, PublicSseEventBase
from ..builders import EventBuilder
from ..state import ProjectionState
from ..utils import as_dict, coerce_str


def project_terminal_errors(
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

