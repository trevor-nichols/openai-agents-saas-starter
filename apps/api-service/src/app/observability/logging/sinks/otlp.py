"""OTLP JSON-over-HTTP sink."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.settings import Settings
from app.observability.logging.sinks.base import SinkConfig


class OTLPHTTPLogHandler(logging.Handler):
    """Lightweight OTLP JSON-over-HTTP handler for log export."""

    def __init__(self, endpoint: str, headers: Mapping[str, str] | None = None) -> None:
        super().__init__()
        if not endpoint:
            raise ValueError(
                "OTLP endpoint is required when LOGGING_SINKS includes otlp"
            )
        self._endpoint = endpoint
        self._client = httpx.Client(timeout=2.0)
        self._headers = {"Content-Type": "application/json"}
        if headers:
            self._headers.update(headers)

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - network handler
        try:
            entry = json.loads(self.format(record))
            payload = _to_otlp_payload(entry)
            response = self._client.post(self._endpoint, json=payload, headers=self._headers)
            response.raise_for_status()
        except Exception:
            self.handleError(record)

    def close(self) -> None:  # pragma: no cover - resource cleanup
        self._client.close()
        super().close()


def build_otlp_sink(
    settings: Settings,
    log_level: str,
    formatter_ref: str,
    *,
    file_selected: bool,
) -> SinkConfig:
    _ = file_selected
    if not settings.logging_otlp_endpoint:
        raise ValueError(
            "LOGGING_OTLP_ENDPOINT is required when LOGGING_SINKS includes otlp"
        )
    headers = parse_headers(settings.logging_otlp_headers) or {}
    handlers = {
        "otlp": {
            "class": "app.observability.logging.sinks.otlp.OTLPHTTPLogHandler",
            "level": log_level,
            "formatter": formatter_ref,
            "endpoint": settings.logging_otlp_endpoint,
            "headers": headers,
        }
    }
    return SinkConfig(handlers=handlers, root_handlers=["otlp"])


def parse_headers(raw_headers: str | None) -> dict[str, str] | None:
    if not raw_headers:
        return None
    try:
        parsed = json.loads(raw_headers)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError("LOGGING_OTLP_HEADERS must be valid JSON") from exc
    if not isinstance(parsed, Mapping):
        raise ValueError("LOGGING_OTLP_HEADERS must decode to an object")
    return {str(key): str(value) for key, value in parsed.items()}


def _to_otlp_payload(entry: dict[str, Any]) -> dict[str, Any]:
    timestamp = entry.get("ts")
    if isinstance(timestamp, str):
        try:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
        except ValueError:
            ts = datetime.now(UTC).timestamp()
    else:
        ts = datetime.now(UTC).timestamp()
    nanos = int(ts * 1_000_000_000)

    attributes = []
    for key, value in entry.items():
        if key in {"ts", "level", "logger", "service", "environment", "message"}:
            continue
        attributes.append({"key": key, "value": _otlp_any_value(value)})

    body_value = entry.get("message") or entry.get("event") or "log"

    return {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        {
                            "key": "service.name",
                            "value": {"stringValue": entry.get("service")},
                        },
                        {
                            "key": "deployment.environment",
                            "value": {"stringValue": entry.get("environment")},
                        },
                    ]
                },
                "scopeLogs": [
                    {
                        "scope": {"name": entry.get("logger", "api-service")},
                        "logRecords": [
                            {
                                "timeUnixNano": str(nanos),
                                "severityText": str(entry.get("level", "INFO")).upper(),
                                "body": {"stringValue": str(body_value)},
                                "attributes": attributes,
                            }
                        ],
                    }
                ],
            }
        ]
    }


def _otlp_any_value(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int | float):
        return {"doubleValue": float(value)}
    if isinstance(value, Mapping):
        return {"stringValue": json.dumps(value)}
    return {"stringValue": str(value)}


__all__ = ["OTLPHTTPLogHandler", "build_otlp_sink", "parse_headers"]
