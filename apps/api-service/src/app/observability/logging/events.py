"""Convenience helpers for emitting structured log events."""

from __future__ import annotations

from typing import Any

from starter_contracts.observability.logging.events import log_event as _log_event


def log_event(
    event: str,
    *,
    level: str = "info",
    message: str | None = None,
    exc_info: Any | None = None,
    **fields: Any,
) -> None:
    """Emit a structured log event with contextual metadata."""

    _log_event(
        event,
        level=level,
        message=message,
        exc_info=exc_info,
        logger_name="api-service.observability",
        **fields,
    )


__all__ = ["log_event"]
