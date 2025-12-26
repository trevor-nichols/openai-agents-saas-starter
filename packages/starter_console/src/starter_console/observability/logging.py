"""Console logging configuration and Textual integration."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from starter_contracts.observability.logging import (
    LoggingRuntimeConfig,
    configure_logging,
    log_event,
)
from starter_contracts.observability.logging.sinks.file import ensure_log_paths

from starter_console.core import CLIContext

CONSOLE_COMPONENT = "starter-console"


@dataclass(slots=True)
class ConsoleLoggingConfig:
    runtime: LoggingRuntimeConfig
    textual_log_path: Path | None


def configure_console_logging(ctx: CLIContext) -> ConsoleLoggingConfig:
    runtime = _build_runtime_config(ctx)
    configure_logging(runtime)
    textual_log_path = _resolve_textual_log_path(runtime)
    return ConsoleLoggingConfig(runtime=runtime, textual_log_path=textual_log_path)


def configure_textual_logging(
    ctx: CLIContext,
    *,
    runtime: LoggingRuntimeConfig | None = None,
) -> None:
    resolved = runtime or _build_runtime_config(ctx)
    log_path = _resolve_textual_log_path(resolved)
    if log_path is not None:
        os.environ.setdefault("TEXTUAL_LOG", str(log_path))
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            ctx.console.warn(
                f"Unable to create Textual log directory at {log_path.parent}: {exc}",
                topic="tui",
            )

    _attach_textual_log_bridge()


def _build_runtime_config(ctx: CLIContext) -> LoggingRuntimeConfig:
    env = os.environ

    def _pick(*keys: str, default: str | None = None) -> str | None:
        for key in keys:
            value = env.get(key)
            if value not in (None, ""):
                return value
        return default

    def _as_int(value: str | None, default: int) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def _as_bool(value: str | None, default: bool) -> bool:
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    service = _pick("CONSOLE_SERVICE_NAME", default="starter-console")
    environment = _pick("ENVIRONMENT", default="development")
    log_level = _pick("CONSOLE_LOG_LEVEL", "LOG_LEVEL", default="INFO")
    logging_sinks = _pick("CONSOLE_LOGGING_SINKS", default="file")
    log_root = _pick("CONSOLE_LOG_ROOT", "LOG_ROOT")

    logging_file_path = _pick(
        "CONSOLE_LOGGING_FILE_PATH", default="var/log/starter-console.log"
    )
    logging_file_max_mb = _as_int(
        _pick("CONSOLE_LOGGING_FILE_MAX_MB", "LOGGING_FILE_MAX_MB"), 10
    )
    logging_file_backups = _as_int(
        _pick("CONSOLE_LOGGING_FILE_BACKUPS", "LOGGING_FILE_BACKUPS"), 5
    )
    logging_max_days = _as_int(
        _pick("CONSOLE_LOGGING_MAX_DAYS", "LOGGING_MAX_DAYS"), 0
    )
    logging_duplex_error_file = _as_bool(
        _pick("CONSOLE_LOGGING_DUPLEX_ERROR_FILE", "LOGGING_DUPLEX_ERROR_FILE"),
        False,
    )

    logging_datadog_api_key = _pick(
        "CONSOLE_LOGGING_DATADOG_API_KEY", "LOGGING_DATADOG_API_KEY"
    )
    logging_datadog_site = _pick(
        "CONSOLE_LOGGING_DATADOG_SITE", "LOGGING_DATADOG_SITE", default="datadoghq.com"
    )
    logging_otlp_endpoint = _pick(
        "CONSOLE_LOGGING_OTLP_ENDPOINT", "LOGGING_OTLP_ENDPOINT"
    )
    logging_otlp_headers = _pick(
        "CONSOLE_LOGGING_OTLP_HEADERS", "LOGGING_OTLP_HEADERS"
    )

    return LoggingRuntimeConfig(
        service=service or "starter-console",
        environment=environment or "development",
        log_level=log_level or "INFO",
        logging_sinks=logging_sinks or "file",
        log_root=log_root,
        logging_file_path=logging_file_path or "var/log/starter-console.log",
        logging_file_max_mb=logging_file_max_mb,
        logging_file_backups=logging_file_backups,
        logging_max_days=logging_max_days,
        logging_duplex_error_file=logging_duplex_error_file,
        logging_datadog_api_key=logging_datadog_api_key,
        logging_datadog_site=logging_datadog_site,
        logging_otlp_endpoint=logging_otlp_endpoint,
        logging_otlp_headers=logging_otlp_headers,
        component=CONSOLE_COMPONENT,
        handler_namespace="starter_contracts.observability.logging.sinks",
        default_file_path="var/log/starter-console.log",
        repo_root=ctx.project_root,
    )


def _resolve_textual_log_path(runtime: LoggingRuntimeConfig) -> Path | None:
    try:
        paths = ensure_log_paths(runtime)
    except Exception:
        return None
    return paths.component_root / "textual.log"


class _TextualLogBridge(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
        except Exception:
            message = str(record.msg)

        log_event(
            "console.textual",
            level=record.levelname.lower(),
            message=message,
            exc_info=record.exc_info,
            logger_name="starter-console.observability",
            textual_logger=record.name,
            textual_level=record.levelname,
            textual_module=record.module,
            textual_line=record.lineno,
        )


def _attach_textual_log_bridge() -> None:
    logger = logging.getLogger("textual")
    if any(isinstance(handler, _TextualLogBridge) for handler in logger.handlers):
        return

    logger.addHandler(_TextualLogBridge())
    if logger.level == logging.NOTSET:
        logger.setLevel(_resolve_textual_level())
    logger.propagate = False


def _resolve_textual_level() -> int:
    env_level = os.getenv("CONSOLE_TEXTUAL_LOG_LEVEL") or os.getenv("TEXTUAL_LOG_LEVEL")
    if env_level:
        try:
            return int(env_level)
        except ValueError:
            normalized = env_level.upper()
            levels = {
                "CRITICAL": logging.CRITICAL,
                "ERROR": logging.ERROR,
                "WARNING": logging.WARNING,
                "WARN": logging.WARNING,
                "INFO": logging.INFO,
                "DEBUG": logging.DEBUG,
            }
            return levels.get(normalized, logging.INFO)
    return logging.INFO


__all__ = ["configure_console_logging", "configure_textual_logging", "ConsoleLoggingConfig"]
