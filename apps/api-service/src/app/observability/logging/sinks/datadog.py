"""Datadog HTTP intake sink."""

from __future__ import annotations

import json
import logging

import httpx

from app.core.settings import Settings
from app.observability.logging.sinks.base import SinkConfig


class DatadogHTTPLogHandler(logging.Handler):
    """Minimal Datadog HTTP intake handler."""

    def __init__(self, api_key: str, site: str = "datadoghq.com") -> None:
        super().__init__()
        if not api_key:
            raise ValueError("Datadog API key is required when logging_sink=datadog")
        self._endpoint = f"https://http-intake.logs.{site}/api/v2/logs"
        self._client = httpx.Client(timeout=2.0)
        self._headers = {
            "DD-API-KEY": api_key,
            "Content-Type": "application/json",
        }

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - network handler
        try:
            payload = self.format(record)
            body = json.dumps([json.loads(payload)]).encode("utf-8")
            response = self._client.post(self._endpoint, content=body, headers=self._headers)
            response.raise_for_status()
        except Exception:
            self.handleError(record)

    def close(self) -> None:  # pragma: no cover - resource cleanup
        self._client.close()
        super().close()


def build_datadog_sink(
    settings: Settings,
    log_level: str,
    formatter_ref: str,
    *,
    file_selected: bool,
) -> SinkConfig:
    _ = file_selected
    if not settings.logging_datadog_api_key:
        raise ValueError("LOGGING_DATADOG_API_KEY is required when LOGGING_SINK=datadog")
    handlers = {
        "datadog": {
            "class": "app.observability.logging.sinks.datadog.DatadogHTTPLogHandler",
            "level": log_level,
            "formatter": formatter_ref,
            "api_key": settings.logging_datadog_api_key,
            "site": settings.logging_datadog_site or "datadoghq.com",
        }
    }
    return SinkConfig(handlers=handlers, root_handlers=["datadog"])


__all__ = ["DatadogHTTPLogHandler", "build_datadog_sink"]
