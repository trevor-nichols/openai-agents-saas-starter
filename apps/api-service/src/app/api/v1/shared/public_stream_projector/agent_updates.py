from __future__ import annotations

from app.domain.ai.models import AgentStreamEvent

from ..streaming import AgentUpdatedEvent, PublicSseEventBase
from .builders import EventBuilder
from .state import ProjectionState


def project_event(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if event.kind != "agent_updated_stream_event" or not event.new_agent:
        return []

    from_agent = state.current_agent
    to_agent = event.new_agent
    if from_agent == to_agent:
        state.current_agent = to_agent
        return []

    state.current_agent = to_agent
    state.handoff_count += 1
    return [
        AgentUpdatedEvent(
            **builder.base(kind="agent.updated"),
            from_agent=from_agent,
            to_agent=to_agent,
            handoff_index=state.handoff_count,
        )
    ]

