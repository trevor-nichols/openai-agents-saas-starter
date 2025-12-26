"""Logging configuration assembly for dictConfig."""

from __future__ import annotations

import logging
import logging.config
from dataclasses import asdict
from typing import Any

from starter_contracts.observability.logging.formatting import StructuredLoggingConfig
from starter_contracts.observability.logging.sinks import SINK_BUILDERS
from starter_contracts.observability.logging.sinks.base import LoggingRuntimeConfig, SinkConfig

ALLOWED_SINKS = {"stdout", "console", "file", "datadog", "otlp", "none"}


def configure_logging(config: LoggingRuntimeConfig) -> None:
    """Apply JSON logging configuration based on deployment settings."""

    sinks = _parse_sinks(config.logging_sinks)
    log_level = (config.log_level or "INFO").upper()
    formatter_ref = "json"

    handlers, root_handlers = _resolve_handler_configs(sinks, config, log_level, formatter_ref)
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            formatter_ref: {
                "()": "starter_contracts.observability.logging.formatting.JSONLogFormatter",
                "config": asdict(
                    StructuredLoggingConfig(
                        service=config.service,
                        environment=config.environment,
                    )
                ),
            }
        },
        "handlers": handlers,
        "root": {"level": log_level, "handlers": root_handlers},
    }
    logging.config.dictConfig(logging_config)
    # Suppress verbose HTTP client logs to prevent infinite recursion when OTLP sink
    # is enabled (httpx/httpcore debug logs would trigger more OTLP sends).
    for logger_name in ("httpx", "httpcore"):
        logging.getLogger(logger_name).setLevel(
            max(logging.WARNING, logging.getLogger(logger_name).level)
        )


def _parse_sinks(raw: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if raw is None:
        parts: list[str] = ["stdout"]
    elif isinstance(raw, str):
        parts = [part.strip().lower() for part in raw.split(",") if part.strip()]
    else:
        parts = [str(value).strip().lower() for value in raw if str(value).strip()]

    if not parts:
        raise ValueError("At least one logging sink must be specified.")

    deduped: list[str] = []
    for sink in parts:
        if sink not in ALLOWED_SINKS:
            raise ValueError(
                f"Unsupported LOGGING_SINKS entry '{sink}'. Expected one of {ALLOWED_SINKS}."
            )
        if sink == "none" and len(parts) > 1:
            raise ValueError("LOGGING_SINKS cannot include 'none' with other sinks.")
        if sink not in deduped:
            deduped.append(sink)

    return deduped


def _resolve_handler_configs(
    sinks: list[str],
    config: LoggingRuntimeConfig,
    log_level: str,
    formatter_ref: str,
) -> tuple[dict[str, Any], list[str]]:
    handlers: dict[str, Any] = {}
    root_handlers: list[str] = []
    file_selected = "file" in sinks

    for sink in sinks:
        builder = SINK_BUILDERS.get(sink)
        if builder is None:
            raise ValueError(f"Unsupported LOGGING_SINKS entry '{sink}'.")
        sink_cfg: SinkConfig = builder(
            config=config,
            log_level=log_level,
            formatter_ref=formatter_ref,
            file_selected=file_selected,
        )
        for name, cfg in sink_cfg.handlers.items():
            if name in handlers:
                raise ValueError(f"Duplicate handler name '{name}' while configuring sinks {sinks}")
            handlers[name] = cfg
        root_handlers.extend(sink_cfg.root_handlers)

    root_handlers = list(dict.fromkeys(root_handlers))
    return handlers, root_handlers


__all__ = ["configure_logging", "ALLOWED_SINKS"]
