"""Sink registry for structured logging."""

from __future__ import annotations

from starter_contracts.observability.logging.sinks.base import (
    LoggingRuntimeConfig,
    SinkBuilder,
    SinkConfig,
)
from starter_contracts.observability.logging.sinks.datadog import build_datadog_sink
from starter_contracts.observability.logging.sinks.file import build_file_sink
from starter_contracts.observability.logging.sinks.otlp import build_otlp_sink
from starter_contracts.observability.logging.sinks.stdout import build_stdout_sink


def build_null_sink(
    config: LoggingRuntimeConfig, log_level: str, formatter_ref: str, *, file_selected: bool
) -> SinkConfig:
    _ = (config, formatter_ref, file_selected)
    return SinkConfig(
        handlers={"null": {"class": "logging.NullHandler", "level": log_level}},
        root_handlers=["null"],
    )


SINK_BUILDERS: dict[str, SinkBuilder] = {
    "stdout": build_stdout_sink,
    "console": build_stdout_sink,
    "file": build_file_sink,
    "datadog": build_datadog_sink,
    "otlp": build_otlp_sink,
    "none": build_null_sink,
}

__all__ = ["SINK_BUILDERS", "SinkConfig", "SinkBuilder", "LoggingRuntimeConfig"]
