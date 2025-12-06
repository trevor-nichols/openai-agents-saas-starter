"""Convenience helpers for emitting structured log events."""

from __future__ import annotations

import logging
from typing import Any

from app.observability.logging.formatting import clean_fields

LOGGER = logging.getLogger("api-service.observability")


def log_event(
    event: str,
    *,
    level: str = "info",
    message: str | None = None,
    exc_info: Any | None = None,
    **fields: Any,
) -> None:
    """Emit a structured log event with contextual metadata."""

    sanitized_fields = clean_fields(fields)
    payload: dict[str, Any] = {"event": event}
    if sanitized_fields:
        payload["fields"] = sanitized_fields
        payload.update(sanitized_fields)
    if message:
        payload["message"] = message

    extra = {"structured": payload}
    normalized_exc = _normalize_exc_info(exc_info)
    log_fn = getattr(LOGGER, level.lower(), LOGGER.info)
    log_fn(message or event, exc_info=normalized_exc, extra=extra)


def _normalize_exc_info(exc_info: Any) -> Any:
    if exc_info in (None, False):
        return None
    if exc_info is True:
        return True
    if isinstance(exc_info, tuple):
        return exc_info
    if isinstance(exc_info, BaseException):
        return (exc_info.__class__, exc_info, exc_info.__traceback__)
    return exc_info


__all__ = ["log_event"]
