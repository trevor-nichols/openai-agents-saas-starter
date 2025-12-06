"""Sink registry for structured logging."""

from __future__ import annotations

from app.core.settings import Settings
from app.observability.logging.sinks.base import SinkBuilder, SinkConfig
from app.observability.logging.sinks.datadog import build_datadog_sink
from app.observability.logging.sinks.file import build_file_sink
from app.observability.logging.sinks.otlp import build_otlp_sink
from app.observability.logging.sinks.stdout import build_stdout_sink


def build_null_sink(
    settings: Settings, log_level: str, formatter_ref: str, *, file_selected: bool
) -> SinkConfig:
    _ = (settings, formatter_ref, file_selected)
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

__all__ = ["SINK_BUILDERS", "SinkConfig", "SinkBuilder"]
