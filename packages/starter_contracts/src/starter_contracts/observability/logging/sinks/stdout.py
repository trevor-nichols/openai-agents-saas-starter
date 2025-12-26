"""Stdout/console logging sink."""

from __future__ import annotations

from starter_contracts.observability.logging.sinks.base import (
    LoggingRuntimeConfig,
    SinkConfig,
)
from starter_contracts.observability.logging.sinks.file import (
    build_rotating_handler,
    ensure_log_paths,
)


def build_stdout_sink(
    config: LoggingRuntimeConfig,
    log_level: str,
    formatter_ref: str,
    *,
    file_selected: bool,
) -> SinkConfig:
    handlers = {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": log_level,
            "formatter": formatter_ref,
        }
    }
    root_handlers = ["stdout"]

    if config.logging_duplex_error_file and not file_selected:
        paths = ensure_log_paths(config)
        handlers["stderr_file"] = build_rotating_handler(
            paths.error_log,
            config=config,
            level="ERROR",
            formatter=formatter_ref,
            error_only=True,
            use_custom_path=paths.use_custom_path,
        )
        root_handlers.append("stderr_file")

    return SinkConfig(handlers=handlers, root_handlers=root_handlers)


__all__ = ["build_stdout_sink"]
