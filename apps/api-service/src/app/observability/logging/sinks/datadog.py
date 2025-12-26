"""Datadog HTTP intake sink."""

from starter_contracts.observability.logging.sinks.datadog import (
    DatadogHTTPLogHandler,
    build_datadog_sink,
)

__all__ = ["DatadogHTTPLogHandler", "build_datadog_sink"]
