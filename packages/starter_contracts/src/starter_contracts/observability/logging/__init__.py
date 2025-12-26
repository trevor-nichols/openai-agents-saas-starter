"""Structured logging package with modular sinks and context helpers."""

from starter_contracts.observability.logging.config import configure_logging
from starter_contracts.observability.logging.context import (
    bind_log_context,
    clear_log_context,
    get_log_context,
    log_context,
)
from starter_contracts.observability.logging.events import log_event
from starter_contracts.observability.logging.formatting import (
    JSONLogFormatter,
    StructuredLoggingConfig,
)
from starter_contracts.observability.logging.sinks.base import LoggingRuntimeConfig
from starter_contracts.observability.logging.sinks.file import DateRollingFileHandler

__all__ = [
    "configure_logging",
    "log_event",
    "log_context",
    "bind_log_context",
    "clear_log_context",
    "get_log_context",
    "JSONLogFormatter",
    "StructuredLoggingConfig",
    "LoggingRuntimeConfig",
    "DateRollingFileHandler",
]
