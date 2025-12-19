"""Guardrail event emission utilities for streaming surfaces."""

from __future__ import annotations

import contextvars
from collections.abc import Callable, Mapping, MutableMapping
from typing import Any

# Callable signature: (payload: Mapping[str, Any]) -> None
_guardrail_emitter: contextvars.ContextVar[
    Callable[[Mapping[str, Any]], None] | None
] = contextvars.ContextVar("guardrail_event_emitter", default=None)

# Collector list used to build final summaries
_guardrail_collector: contextvars.ContextVar[list[Mapping[str, Any]] | None] = (
    contextvars.ContextVar("guardrail_event_collector", default=None)
)

# Optional contextual metadata to stamp onto guardrail events (conversation, etc.)
_guardrail_context: contextvars.ContextVar[MutableMapping[str, Any]] = contextvars.ContextVar(
    "guardrail_event_context", default={}
)


class GuardrailEmissionToken:
    """Token for resetting guardrail emission context."""

    def __init__(self, emitter_token, collector_token, context_token) -> None:
        self._emitter_token = emitter_token
        self._collector_token = collector_token
        self._context_token = context_token

    def reset(self) -> None:
        if self._emitter_token:
            _guardrail_emitter.reset(self._emitter_token)
        if self._collector_token:
            _guardrail_collector.reset(self._collector_token)
        if self._context_token:
            _guardrail_context.reset(self._context_token)


def set_guardrail_emitters(
    *,
    emitter: Callable[[Mapping[str, Any]], None] | None,
    collector: list[Mapping[str, Any]] | None,
    context: Mapping[str, Any] | None = None,
) -> GuardrailEmissionToken:
    """Install emitter + collector for the current context."""

    emitter_token = _guardrail_emitter.set(emitter)
    collector_token = _guardrail_collector.set(collector)
    context_token = _guardrail_context.set(dict(context or {}))
    return GuardrailEmissionToken(emitter_token, collector_token, context_token)


def emit_guardrail_event(payload: Mapping[str, Any]) -> None:
    """Emit a guardrail event to the active sink and collector."""
    emitter = _guardrail_emitter.get()
    collector = _guardrail_collector.get()
    context = _guardrail_context.get() or {}

    enriched = {**context, **payload} if context else dict(payload)

    if collector is not None:
        collector.append(enriched)
    if emitter is not None:
        try:
            emitter(enriched)
        except Exception:
            # Do not let guardrail emission break main flow
            return


__all__ = ["set_guardrail_emitters", "emit_guardrail_event", "GuardrailEmissionToken"]
