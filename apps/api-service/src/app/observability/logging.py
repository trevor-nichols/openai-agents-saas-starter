"""Structured logging helpers, context propagation, and sink configuration."""

from __future__ import annotations

import json
import logging
import logging.config
import logging.handlers
import shutil
import threading
from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.core.settings import Settings

LOGGER = logging.getLogger("api-service.observability")
_LOG_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("structured_log_context", default={})


@dataclass(slots=True)
class StructuredLoggingConfig:
    service: str
    environment: str


_config = StructuredLoggingConfig(service="api-service", environment="development")


@dataclass(slots=True)
class LogPaths:
    """Resolved log directories and files for the current process."""

    base_root: Path
    date_root: Path
    component_root: Path
    all_log: Path
    error_log: Path
    use_custom_path: bool


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, set | frozenset):
        return sorted(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value


def _clean(data: Mapping[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        cleaned[key] = _serialize(value)
    return cleaned


def get_log_context() -> dict[str, Any]:
    """Return a shallow copy of the current log context."""

    return dict(_LOG_CONTEXT.get())


@contextmanager
def log_context(**fields: Any):
    """Temporarily extend the structured log context within the active task."""

    current = _LOG_CONTEXT.get()
    merged = current | _clean(fields)
    token = _LOG_CONTEXT.set(merged)
    try:
        yield
    finally:
        _LOG_CONTEXT.reset(token)


def bind_log_context(**fields: Any) -> None:
    """Merge persistent context into the current task scope."""

    current = _LOG_CONTEXT.get()
    merged = current | _clean(fields)
    _LOG_CONTEXT.set(merged)


def clear_log_context(*keys: str) -> None:
    """Remove keys from the current log context or reset entirely when no keys provided."""

    if not keys:
        _LOG_CONTEXT.set({})
        return
    current = dict(_LOG_CONTEXT.get())
    for key in keys:
        current.pop(key, None)
    _LOG_CONTEXT.set(current)


class JSONLogFormatter(logging.Formatter):
    """Emit structured JSON with context + event metadata."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any]
        structured = getattr(record, "structured", None)
        if isinstance(structured, dict):
            payload = dict(structured)
        else:
            message = record.getMessage()
            payload = {"event": record.name, "message": message or record.name}

        context = _clean(_LOG_CONTEXT.get())
        for key, value in context.items():
            payload.setdefault(key, value)

        payload.setdefault("message", record.getMessage())
        payload.setdefault("event", payload.get("message"))

        fields = payload.get("fields")
        if isinstance(fields, Mapping):
            payload["fields"] = _clean(fields)

        payload.setdefault("service", _config.service)
        payload.setdefault("environment", _config.environment)

        base = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname.lower(),
            "logger": record.name,
        }
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            payload.setdefault("exc_type", getattr(exc_type, "__name__", str(exc_type)))
            payload.setdefault("exc_message", str(exc_value))
            payload.setdefault("exc_traceback", self.formatException(record.exc_info))

        envelope = base | payload
        return json.dumps(envelope, default=_serialize, separators=(",", ":"))


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


class OTLPHTTPLogHandler(logging.Handler):
    """Lightweight OTLP JSON-over-HTTP handler for log export."""

    def __init__(self, endpoint: str, headers: Mapping[str, str] | None = None) -> None:
        super().__init__()
        if not endpoint:
            raise ValueError("OTLP endpoint is required when logging_sink=otlp")
        self._endpoint = endpoint
        self._client = httpx.Client(timeout=2.0)
        self._headers = {"Content-Type": "application/json"}
        if headers:
            self._headers.update(headers)

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - network handler
        try:
            entry = json.loads(self.format(record))
            payload = _to_otlp_payload(entry)
            response = self._client.post(self._endpoint, json=payload, headers=self._headers)
            response.raise_for_status()
        except Exception:
            self.handleError(record)

    def close(self) -> None:  # pragma: no cover - resource cleanup
        self._client.close()
        super().close()


def _to_otlp_payload(entry: dict[str, Any]) -> dict[str, Any]:
    timestamp = entry.get("ts")
    if isinstance(timestamp, str):
        try:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
        except ValueError:
            ts = datetime.now(UTC).timestamp()
    else:
        ts = datetime.now(UTC).timestamp()
    nanos = int(ts * 1_000_000_000)

    attributes = []
    for key, value in entry.items():
        if key in {"ts", "level", "logger", "service", "environment", "message"}:
            continue
        attributes.append({"key": key, "value": _otlp_any_value(value)})

    body_value = entry.get("message") or entry.get("event") or "log"

    return {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        {
                            "key": "service.name",
                            "value": {"stringValue": entry.get("service", _config.service)},
                        },
                        {
                            "key": "deployment.environment",
                            "value": {"stringValue": entry.get("environment", _config.environment)},
                        },
                    ]
                },
                "scopeLogs": [
                    {
                        "scope": {"name": entry.get("logger", "api-service")},
                        "logRecords": [
                            {
                                "timeUnixNano": str(nanos),
                                "severityText": str(entry.get("level", "INFO")).upper(),
                                "body": {"stringValue": str(body_value)},
                                "attributes": attributes,
                            }
                        ],
                    }
                ],
            }
        ]
    }


def _otlp_any_value(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int | float):
        return {"doubleValue": float(value)}
    if isinstance(value, Mapping):
        return {"stringValue": json.dumps(_clean(value), default=_serialize)}
    return {"stringValue": str(value)}


def configure_logging(settings: Settings) -> None:
    """Apply JSON logging configuration based on deployment settings."""

    global _config
    _config = StructuredLoggingConfig(
        service=settings.app_name,
        environment=settings.environment,
    )

    sink = (settings.logging_sink or "stdout").strip().lower()
    log_level = (settings.log_level or "INFO").upper()

    handlers, root_handlers = _resolve_handler_configs(sink, settings, log_level)
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": "app.observability.logging.JSONLogFormatter"}},
        "handlers": handlers,
        "root": {"level": log_level, "handlers": root_handlers},
    }
    logging.config.dictConfig(logging_config)
    logging.getLogger("httpx").setLevel(max(logging.WARNING, logging.getLogger("httpx").level))


def _resolve_handler_configs(
    sink: str,
    settings: Settings,
    log_level: str,
) -> tuple[dict[str, Any], list[str]]:
    formatter_ref = "json"
    handlers: dict[str, Any] = {}
    root_handlers: list[str] = []

    if sink in {"stdout", "console"}:
        handlers["stdout"] = {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": log_level,
            "formatter": formatter_ref,
        }
        root_handlers.append("stdout")
        if settings.logging_duplex_error_file:
            paths = _ensure_log_paths(settings, component="api")
            handlers["stderr_file"] = _build_rotating_handler(
                paths.error_log,
                level="ERROR",
                formatter=formatter_ref,
                settings=settings,
                error_only=True,
                use_custom_path=paths.use_custom_path,
            )
            root_handlers.append("stderr_file")
        return handlers, root_handlers

    if sink == "none":
        handlers["null"] = {
            "class": "logging.NullHandler",
            "level": log_level,
        }
        root_handlers.append("null")
        return handlers, root_handlers

    if sink == "file":
        paths = _ensure_log_paths(settings, component="api", ensure_component=True)
        handlers["file_all"] = _build_rotating_handler(
            paths.all_log,
            level=log_level,
            formatter=formatter_ref,
            settings=settings,
            use_custom_path=paths.use_custom_path,
        )
        handlers["file_error"] = _build_rotating_handler(
            paths.error_log,
            level="ERROR",
            formatter=formatter_ref,
            settings=settings,
            error_only=True,
            use_custom_path=paths.use_custom_path,
        )
        root_handlers.extend(["file_all", "file_error"])
        return handlers, root_handlers

    if sink == "datadog":
        if not settings.logging_datadog_api_key:
            raise ValueError("LOGGING_DATADOG_API_KEY is required when LOGGING_SINK=datadog")
        handlers["datadog"] = {
            "class": "app.observability.logging.DatadogHTTPLogHandler",
            "level": log_level,
            "formatter": formatter_ref,
            "api_key": settings.logging_datadog_api_key,
            "site": settings.logging_datadog_site or "datadoghq.com",
        }
        root_handlers.append("datadog")
        return handlers, root_handlers

    if sink == "otlp":
        if not settings.logging_otlp_endpoint:
            raise ValueError("LOGGING_OTLP_ENDPOINT is required when LOGGING_SINK=otlp")
        headers = _parse_headers(settings.logging_otlp_headers)
        handlers["otlp"] = {
            "class": "app.observability.logging.OTLPHTTPLogHandler",
            "level": log_level,
            "formatter": formatter_ref,
            "endpoint": settings.logging_otlp_endpoint,
            "headers": headers,
        }
        root_handlers.append("otlp")
        return handlers, root_handlers

    raise ValueError(
        f"Unsupported LOGGING_SINK '{sink}'. Expected stdout, file, datadog, otlp, or none."
    )


def _parse_headers(raw_headers: str | None) -> dict[str, str] | None:
    if not raw_headers:
        return None
    try:
        parsed = json.loads(raw_headers)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError("LOGGING_OTLP_HEADERS must be valid JSON") from exc
    if not isinstance(parsed, Mapping):
        raise ValueError("LOGGING_OTLP_HEADERS must decode to an object")
    return {str(key): str(value) for key, value in parsed.items()}


def log_event(
    event: str,
    *,
    level: str = "info",
    message: str | None = None,
    exc_info: Any | None = None,
    **fields: Any,
) -> None:
    """Emit a structured log event with contextual metadata."""

    sanitized_fields = _clean(fields)
    payload: dict[str, Any] = {"event": event}
    if sanitized_fields:
        payload["fields"] = sanitized_fields
        payload.update(sanitized_fields)
    if message:
        payload["message"] = message

    extra = {"structured": payload}
    normalized_exc = _normalize_exc_info(exc_info)
    log_fn = getattr(LOGGER, level.lower(), LOGGER.info)
    log_fn(message or event, exc_info=normalized_exc, extra=extra)


def _normalize_exc_info(exc_info: Any) -> Any:
    if exc_info in (None, False):
        return None
    if exc_info is True:
        return True
    if isinstance(exc_info, tuple):
        return exc_info
    if isinstance(exc_info, BaseException):
        return (exc_info.__class__, exc_info, exc_info.__traceback__)
    return exc_info


def _build_rotating_handler(
    path: Path,
    *,
    level: str,
    formatter: str,
    settings: Settings,
    error_only: bool = False,
    use_custom_path: bool = False,
) -> dict[str, Any]:
    max_bytes = int(settings.logging_file_max_mb * 1024 * 1024)
    log_root_value = None if use_custom_path else (settings.log_root or "var/log")
    return {
        "class": "app.observability.logging.DateRollingFileHandler",
        "level": level,
        "formatter": formatter,
        "filename_base": str(path),
        "log_root": log_root_value,
        "component": "api",
        "max_bytes": max_bytes,
        "backup_count": settings.logging_file_backups,
        "logging_max_days": int(settings.logging_max_days or 0),
        "error_only": error_only,
    }


def _ensure_log_paths(
    settings: Settings,
    *,
    component: str,
    ensure_component: bool = False,
) -> LogPaths:
    default_path = "var/log/api-service.log"
    log_path_value = settings.logging_file_path
    use_custom_path = bool(log_path_value) and str(log_path_value) != default_path

    if use_custom_path:
        custom = Path(log_path_value).expanduser()
        all_path = custom if custom.is_absolute() else (Path.cwd() / custom).resolve()
        component_root = all_path.parent
        component_root.mkdir(parents=True, exist_ok=True)
        base_root = component_root
        date_root = component_root
    else:
        base_root = Path(settings.log_root or "var/log").expanduser()
        today = date.today().isoformat()
        date_root = base_root / today
        component_root = date_root / component
        component_root.mkdir(parents=True, exist_ok=True)
        _update_current_symlink(base_root, date_root)
        if settings.logging_max_days:
            _maybe_prune_logs(base_root, int(settings.logging_max_days))
        all_path = component_root / "all.log"

    error_path = component_root / "error.log"

    return LogPaths(
        base_root=base_root,
        date_root=date_root,
        component_root=component_root,
        all_log=all_path,
        error_log=error_path,
        use_custom_path=use_custom_path,
    )


def _update_current_symlink(base_root: Path, target: Path) -> None:
    current_link = base_root / "current"
    try:
        if current_link.is_symlink() or current_link.exists():
            current_link.unlink()
        current_link.symlink_to(target, target_is_directory=True)
    except OSError:
        # Non-fatal; continue without symlink.
        return


def _maybe_prune_logs(base_root: Path, max_days: int) -> None:
    max_days = int(max_days or 0)
    if max_days <= 0:
        return

    cutoff = date.today() - timedelta(days=max_days)
    for entry in base_root.iterdir():
        if entry.name == "current" or not entry.is_dir():
            continue
        try:
            entry_date = date.fromisoformat(entry.name)
        except ValueError:
            continue
        if entry_date < cutoff:
            shutil.rmtree(entry, ignore_errors=True)


class DateRollingFileHandler(logging.Handler):
    """Rotating file handler that moves to a new dated directory when the day changes."""

    def __init__(
        self,
        *,
        filename_base: str | None,
        log_root: str | None,
        component: str = "api",
        max_bytes: int,
        backup_count: int,
        logging_max_days: int = 0,
        error_only: bool = False,
    ) -> None:
        super().__init__()
        self.filename_base = Path(filename_base) if filename_base else None
        self.log_root = Path(log_root).expanduser() if log_root else None
        self.component = component or "api"
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.logging_max_days = logging_max_days
        self.error_only = error_only
        self._today = date.today
        self._lock = threading.Lock()
        self._delegate: logging.Handler | None = None
        self._current_date: str | None = None
        self._roll_if_needed()

    def emit(self, record: logging.LogRecord) -> None:
        with self._lock:
            self._roll_if_needed()
            if self.error_only and record.levelno < logging.ERROR:
                return
            if self._delegate is not None:
                self._delegate.emit(record)

    def setFormatter(self, fmt: logging.Formatter | None) -> None:
        super().setFormatter(fmt)
        if self._delegate is not None:
            self._delegate.setFormatter(fmt)

    def close(self) -> None:
        with self._lock:
            if self._delegate:
                try:
                    self._delegate.close()
                except Exception:
                    pass
                self._delegate = None
        super().close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _roll_if_needed(self) -> None:
        today = self._today().isoformat()
        if self._delegate is not None and self._current_date == today:
            return

        base_root, date_root, component_root, all_path, error_path = self._resolve_paths(today)
        component_root.mkdir(parents=True, exist_ok=True)
        if self.log_root is not None:
            _update_current_symlink(base_root, date_root)
            if self.logging_max_days:
                _maybe_prune_logs(base_root, self.logging_max_days)

        if self._delegate is not None:
            try:
                self._delegate.close()
            except Exception:
                pass

        target = error_path if self.error_only else all_path
        self._delegate = logging.handlers.RotatingFileHandler(
            filename=str(target),
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            delay=True,
        )
        if self.formatter:
            self._delegate.setFormatter(self.formatter)
        self._current_date = today

    def _resolve_paths(self, today_str: str) -> tuple[Path, Path, Path, Path, Path]:
        if self.log_root is not None:
            base_root = self.log_root
            date_root = base_root / today_str
            component_root = date_root / self.component
            all_path = component_root / "all.log"
            error_path = component_root / "error.log"
            return base_root, date_root, component_root, all_path, error_path

        # Custom static file path: do not use dated layout, symlink, or pruning.
        assert self.filename_base is not None
        all_path = (
            self.filename_base
            if self.filename_base.is_absolute()
            else (Path.cwd() / self.filename_base).resolve()
        )
        component_root = all_path.parent
        date_root = component_root  # placeholder; unused when log_root is None
        base_root = component_root
        error_path = component_root / "error.log"
        return base_root, date_root, component_root, all_path, error_path


__all__ = [
    "JSONLogFormatter",
    "configure_logging",
    "log_event",
    "log_context",
    "bind_log_context",
    "clear_log_context",
    "get_log_context",
]
