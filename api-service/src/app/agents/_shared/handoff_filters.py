"""Central registry for handoff input filters used by AgentSpec declarations."""

from __future__ import annotations

from collections.abc import Callable

from agents.extensions import handoff_filters
from agents.handoffs import HandoffInputData

HandoffFilter = Callable[[HandoffInputData], HandoffInputData]


def _last_turn(data: HandoffInputData) -> HandoffInputData:
    history = data.input_history
    trimmed = history[-2:] if isinstance(history, tuple) and len(history) > 2 else history
    return data.clone(input_history=trimmed)


def _fresh(data: HandoffInputData) -> HandoffInputData:
    return data.clone(input_history=())


FILTERS: dict[str, HandoffFilter] = {
    # Mirrors legacy policy shortcuts
    "full": lambda d: d,
    "fresh": _fresh,
    "last_turn": _last_turn,
    # SDK-provided helpers
    "remove_all_tools": handoff_filters.remove_all_tools,
}


def get_filter(name: str | None) -> HandoffFilter | None:
    if not name:
        return None
    return FILTERS.get(name)


__all__ = ["HandoffFilter", "FILTERS", "get_filter"]
