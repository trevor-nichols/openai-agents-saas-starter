"""Helpers for translating request payloads into runtime options."""

from __future__ import annotations

from typing import Any

from app.domain.ai import RunOptions


def build_run_options(payload: Any, *, hook_sink: Any | None = None) -> RunOptions | None:
    """Map loosely typed payload into strongly typed RunOptions.

    We keep this logic isolated so unit tests can cover the permutations
    without needing the full AgentService harness.
    """

    if not payload:
        return RunOptions(hook_sink=hook_sink) if hook_sink else None

    return RunOptions(
        max_turns=getattr(payload, "max_turns", None),
        previous_response_id=getattr(payload, "previous_response_id", None),
        handoff_input_filter=getattr(payload, "handoff_input_filter", None),
        run_config=getattr(payload, "run_config", None),
        hook_sink=hook_sink,
    )


__all__ = ["build_run_options"]
