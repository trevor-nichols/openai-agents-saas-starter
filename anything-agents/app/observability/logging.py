"""Structured logging helpers for auth observability."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

LOGGER = logging.getLogger("auth.observability")


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, set | frozenset):
        return sorted(value)
    return value


def log_event(
    event: str,
    *,
    level: str = "info",
    exc_info: Any | None = None,
    **fields: Any,
) -> None:
    payload = {"event": event, **fields}
    message = json.dumps(payload, default=_serialize, separators=(",", ":"))
    log_fn = getattr(LOGGER, level, LOGGER.info)
    if exc_info:
        log_fn(message, exc_info=exc_info)
    else:
        log_fn(message)
