"""Sink registry for structured logging."""

from typing import cast

from starter_contracts.observability.logging.sinks import (
    SINK_BUILDERS,
    LoggingRuntimeConfig,
    SinkBuilder,
    SinkConfig,
)
from starter_contracts.observability.logging.sinks import build_null_sink as _build_null_sink
from starter_contracts.observability.logging.sinks.datadog import build_datadog_sink
from starter_contracts.observability.logging.sinks.file import build_file_sink
from starter_contracts.observability.logging.sinks.otlp import build_otlp_sink
from starter_contracts.observability.logging.sinks.stdout import build_stdout_sink

from app.core.settings import Settings


def build_null_sink(
    settings: Settings,
    log_level: str,
    formatter_ref: str,
    *,
    file_selected: bool,
) -> SinkConfig:
    return _build_null_sink(
        cast(LoggingRuntimeConfig, settings),
        log_level,
        formatter_ref,
        file_selected=file_selected,
    )


__all__ = [
    "SINK_BUILDERS",
    "LoggingRuntimeConfig",
    "SinkBuilder",
    "SinkConfig",
    "build_stdout_sink",
    "build_file_sink",
    "build_datadog_sink",
    "build_otlp_sink",
    "build_null_sink",
]
