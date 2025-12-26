"""Context propagation helpers for structured logging."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from starter_contracts.observability.logging.formatting import clean_fields

_LOG_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("structured_log_context", default={})


def get_log_context() -> dict[str, Any]:
    """Return a shallow copy of the current log context."""

    return dict(_LOG_CONTEXT.get())


@contextmanager
def log_context(**fields: Any):
    """Temporarily extend the structured log context within the active task."""

    current = _LOG_CONTEXT.get()
    merged = current | clean_fields(fields)
    token = _LOG_CONTEXT.set(merged)
    try:
        yield
    finally:
        _LOG_CONTEXT.reset(token)


def bind_log_context(**fields: Any) -> None:
    """Merge persistent context into the current task scope."""

    current = _LOG_CONTEXT.get()
    merged = current | clean_fields(fields)
    _LOG_CONTEXT.set(merged)


def clear_log_context(*keys: str) -> None:
    """Remove keys from the current log context or reset entirely when no keys provided."""

    if not keys:
        _LOG_CONTEXT.set({})
        return
    current = dict(_LOG_CONTEXT.get())
    for key in keys:
        current.pop(key, None)
    _LOG_CONTEXT.set(current)


def merge_with_context(structured: Mapping[str, Any]) -> dict[str, Any]:
    """Return structured data merged with the current contextual fields."""

    merged = dict(structured)
    for key, value in clean_fields(get_log_context()).items():
        merged.setdefault(key, value)
    return merged


__all__ = [
    "bind_log_context",
    "clear_log_context",
    "get_log_context",
    "log_context",
    "merge_with_context",
]
