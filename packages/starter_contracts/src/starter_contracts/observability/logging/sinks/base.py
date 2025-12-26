"""Common types for sink builders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(slots=True)
class LoggingRuntimeConfig:
    service: str
    environment: str
    log_level: str
    logging_sinks: str
    log_root: str | None = None
    logging_file_path: str = "var/log/api-service.log"
    logging_file_max_mb: int = 10
    logging_file_backups: int = 5
    logging_max_days: int = 0
    logging_duplex_error_file: bool = False
    logging_datadog_api_key: str | None = None
    logging_datadog_site: str | None = None
    logging_otlp_endpoint: str | None = None
    logging_otlp_headers: str | None = None
    component: str = "api"
    handler_namespace: str = "starter_contracts.observability.logging.sinks"
    default_file_path: str | None = None
    repo_root: Path | None = None
    file_handler_class: str | None = None
    datadog_handler_class: str | None = None
    otlp_handler_class: str | None = None


@dataclass(slots=True)
class SinkConfig:
    handlers: dict[str, Any]
    root_handlers: list[str]


class SinkBuilder(Protocol):
    def __call__(
        self,
        config: LoggingRuntimeConfig,
        log_level: str,
        formatter_ref: str,
        *,
        file_selected: bool,
    ) -> SinkConfig: ...


__all__ = ["LoggingRuntimeConfig", "SinkBuilder", "SinkConfig"]
