"""JSON formatter and value normalization for structured logging."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast


@dataclass(slots=True)
class StructuredLoggingConfig:
    service: str = "api-service"
    environment: str = "development"


def serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, set | frozenset):
        return sorted(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value


def clean_fields(data: Mapping[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        cleaned[key] = serialize(value)
    return cleaned


class JSONLogFormatter(logging.Formatter):
    """Emit structured JSON with context + event metadata."""

    def __init__(
        self,
        config: StructuredLoggingConfig | Mapping[str, str] | None = None,
        context_provider: Callable[[], Mapping[str, Any]] | None = None,
    ) -> None:
        super().__init__()
        if config is None:
            self._config = StructuredLoggingConfig()
        elif isinstance(config, Mapping):
            self._config = StructuredLoggingConfig(**config)
        else:
            self._config = config

        self._context_provider: Callable[[], Mapping[str, Any]]
        if context_provider is None:
            # Lazy import to avoid import cycle
            from app.observability.logging.context import get_log_context

            self._context_provider = cast(Callable[[], Mapping[str, Any]], get_log_context)
        else:
            self._context_provider = context_provider

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any]
        structured = getattr(record, "structured", None)
        if isinstance(structured, dict):
            payload = dict(structured)
        else:
            message = record.getMessage()
            payload = {"event": record.name, "message": message or record.name}

        for key, value in clean_fields(self._context_provider()).items():
            payload.setdefault(key, value)

        payload.setdefault("message", record.getMessage())
        payload.setdefault("event", payload.get("message"))

        fields = payload.get("fields")
        if isinstance(fields, Mapping):
            payload["fields"] = clean_fields(fields)

        payload.setdefault("service", self._config.service)
        payload.setdefault("environment", self._config.environment)

        base = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname.lower(),
            "logger": record.name,
        }
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            payload.setdefault("exc_type", getattr(exc_type, "__name__", str(exc_type)))
            payload.setdefault("exc_message", str(exc_value))
            payload.setdefault("exc_traceback", self.formatException(record.exc_info))

        envelope = base | payload
        return json.dumps(envelope, default=serialize, separators=(",", ":"))


__all__ = ["JSONLogFormatter", "StructuredLoggingConfig", "clean_fields", "serialize"]
