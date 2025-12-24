"""File-based sink with daily directories and rotation."""

from __future__ import annotations

import logging
import logging.handlers
import shutil
import threading
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from app.core.paths import resolve_repo_path
from app.core.settings import Settings
from app.observability.logging.sinks.base import SinkConfig


@dataclass(slots=True)
class LogPaths:
    """Resolved log directories and files for the current process."""

    base_root: Path
    date_root: Path
    component_root: Path
    all_log: Path
    error_log: Path
    use_custom_path: bool


def build_file_sink(
    settings: Settings,
    log_level: str,
    formatter_ref: str,
    *,
    file_selected: bool,  # unused but kept for signature parity
) -> SinkConfig:
    _ = file_selected
    paths = ensure_log_paths(settings, component="api")
    handlers = {
        "file_all": build_rotating_handler(
            paths.all_log,
            level=log_level,
            formatter=formatter_ref,
            settings=settings,
            use_custom_path=paths.use_custom_path,
        ),
        "file_error": build_rotating_handler(
            paths.error_log,
            level="ERROR",
            formatter=formatter_ref,
            settings=settings,
            error_only=True,
            use_custom_path=paths.use_custom_path,
        ),
    }
    return SinkConfig(handlers=handlers, root_handlers=["file_all", "file_error"])


def build_rotating_handler(
    path: Path,
    *,
    level: str,
    formatter: str,
    settings: Settings,
    error_only: bool = False,
    use_custom_path: bool = False,
) -> dict[str, Any]:
    max_bytes = int(settings.logging_file_max_mb * 1024 * 1024)
    log_root_value = None if use_custom_path else str(
        resolve_repo_path(settings.log_root or "var/log")
    )
    return {
        "class": "app.observability.logging.sinks.file.DateRollingFileHandler",
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


def ensure_log_paths(
    settings: Settings,
    *,
    component: str,
) -> LogPaths:
    default_path = "var/log/api-service.log"
    log_path_value = settings.logging_file_path
    use_custom_path = bool(log_path_value) and str(log_path_value) != default_path

    if use_custom_path:
        custom = resolve_repo_path(log_path_value)
        all_path = custom
        component_root = all_path.parent
        component_root.mkdir(parents=True, exist_ok=True)
        base_root = component_root
        date_root = component_root
    else:
        base_root = resolve_repo_path(settings.log_root or "var/log")
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
    "DateRollingFileHandler",
    "LogPaths",
    "build_file_sink",
    "build_rotating_handler",
    "ensure_log_paths",
]
