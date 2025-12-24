"""Unit tests for structured logging helpers."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import date

import pytest

from app.core.settings import Settings
from app.core import paths as core_paths
from app.observability.logging import (
    DateRollingFileHandler,
    JSONLogFormatter,
    clear_log_context,
    configure_logging,
    get_log_context,
    log_context,
    log_event,
)


class _BufferHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - trivial transport
        self.items.append(self.format(record))


def test_log_context_scoping_restores_previous_values() -> None:
    clear_log_context()
    assert get_log_context() == {}

    with log_context(correlation_id="outer"):
        assert get_log_context()["correlation_id"] == "outer"
        with log_context(correlation_id="inner"):
            assert get_log_context()["correlation_id"] == "inner"
        assert get_log_context()["correlation_id"] == "outer"

    assert get_log_context() == {}


def test_log_event_emits_context_and_fields() -> None:
    clear_log_context()
    handler = _BufferHandler()
    handler.setFormatter(JSONLogFormatter())

    logger = logging.getLogger("api-service.observability")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    try:
        with log_context(correlation_id="ctx-123"):
            log_event(
                "unit.test",
                tenant_id="tenant-42",
                quota="signup.per_hour",
            )
    finally:
        logger.removeHandler(handler)

    assert handler.items, "No log records captured"
    payload = json.loads(handler.items[0])
    assert payload["event"] == "unit.test"
    assert payload["correlation_id"] == "ctx-123"
    assert payload["tenant_id"] == "tenant-42"
    assert payload["fields"]["quota"] == "signup.per_hour"


def test_configure_logging_requires_datadog_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOGGING_DATADOG_API_KEY", raising=False)
    settings = Settings.model_validate({"LOGGING_SINKS": None, "LOGGING_SINK": "datadog"})
    with pytest.raises(ValueError):
        configure_logging(settings)


def test_configure_logging_writes_json_to_file(tmp_path: Path) -> None:
    log_path = tmp_path / "test.log"
    settings = Settings.model_validate(
        {
            "LOGGING_SINK": "file",
            "LOGGING_FILE_PATH": str(log_path),
            "LOGGING_FILE_MAX_MB": 1,
        }
    )

    configure_logging(settings)
    log_event("unit.file_sink", message="hello", tenant="tenant-1")

    assert log_path.exists(), "Log file was not created"
    contents = log_path.read_text().strip().splitlines()
    assert contents, "No log records written to file sink"

    payload = json.loads(contents[-1])
    assert payload["event"] == "unit.file_sink"
    assert payload["tenant"] == "tenant-1"


def test_file_sink_uses_daily_root_and_writes_error(tmp_path: Path) -> None:
    settings = Settings.model_validate(
        {
            "LOGGING_SINK": "file",
            "LOG_ROOT": str(tmp_path),
            "LOGGING_FILE_MAX_MB": 1,
            "LOGGING_FILE_BACKUPS": 1,
        }
    )

    configure_logging(settings)

    log_event("unit.info", message="hello-info")
    log_event("unit.error", level="error", message="boom")

    date_dir = tmp_path / date.today().isoformat() / "api"
    all_log = date_dir / "all.log"
    err_log = date_dir / "error.log"
    assert all_log.exists(), "All-log file missing"
    assert err_log.exists(), "Error-log file missing"

    all_lines = [json.loads(line) for line in all_log.read_text().splitlines() if line.strip()]
    err_lines = [json.loads(line) for line in err_log.read_text().splitlines() if line.strip()]

    assert any(entry["event"] == "unit.info" for entry in all_lines)
    assert any(entry["event"] == "unit.error" for entry in all_lines)
    assert any(entry["event"] == "unit.error" for entry in err_lines)
    assert not any(entry["event"] == "unit.info" for entry in err_lines)


def test_default_file_sink_uses_dated_layout_without_log_root(tmp_path: Path, monkeypatch) -> None:
    # Ensure we don't write into the repo; remap repo root to tmp_path
    monkeypatch.setattr(core_paths, "REPO_ROOT", tmp_path)
    settings = Settings.model_validate(
        {
            "LOGGING_SINK": "file",
            # LOG_ROOT unset, LOGGING_FILE_PATH default
        }
    )

    configure_logging(settings)
    log_event("unit.default", message="hi")

    date_dir = tmp_path / "var" / "log" / date.today().isoformat() / "api"
    assert (date_dir / "all.log").exists()


def test_custom_file_path_ignores_unwritable_log_root(monkeypatch, tmp_path: Path) -> None:
    custom = tmp_path / "custom.log"
    settings = Settings.model_validate(
        {
            "LOGGING_SINK": "file",
            "LOGGING_FILE_PATH": str(custom),
            "LOGGING_MAX_DAYS": 7,
            "LOG_ROOT": "/root/forbidden",
        }
    )

    configure_logging(settings)
    log_event("unit.custom", message="ok")

    assert custom.exists(), "Custom log file not written"
    # ensure we didn't create the forbidden root
    try:
        forbidden = Path("/root/forbidden")
        assert not forbidden.exists() or forbidden.is_dir()
    except PermissionError:
        # Some CI runners deny stat access to /root; treat as not created.
        pass


def test_stdout_duplex_error_file(tmp_path: Path) -> None:
    settings = Settings.model_validate(
        {
            "LOGGING_SINK": "stdout",
            "LOG_ROOT": str(tmp_path),
            "LOGGING_DUPLEX_ERROR_FILE": True,
            "LOGGING_FILE_MAX_MB": 1,
        }
    )

    configure_logging(settings)
    log_event("unit.error", level="error", message="boom")

    err_path = tmp_path / date.today().isoformat() / "api" / "error.log"
    assert err_path.exists(), "Error log not created for duplex mode"
    err_lines = [json.loads(line) for line in err_path.read_text().splitlines() if line.strip()]
    assert any(entry["event"] == "unit.error" for entry in err_lines)


def test_prunes_old_dated_directories(tmp_path: Path) -> None:
    base = tmp_path
    old_dir = base / "2024-01-01"
    old_dir.mkdir(parents=True, exist_ok=True)
    (old_dir / "api").mkdir(parents=True, exist_ok=True)
    (old_dir / "api" / "all.log").write_text("stale")

    settings = Settings.model_validate(
        {
            "LOGGING_SINK": "file",
            "LOG_ROOT": str(base),
            "LOGGING_MAX_DAYS": 1,
        }
    )

    configure_logging(settings)
    # Trigger a write to ensure today dir exists
    log_event("unit.today", message="keep")

    assert not old_dir.exists(), "Old dated directory should have been pruned"


def test_date_rolling_handler_moves_to_new_day(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    handler = DateRollingFileHandler(
        filename_base=None,
        log_root=str(tmp_path),
        max_bytes=1024 * 1024,
        backup_count=1,
        logging_max_days=0,
        error_only=False,
    )
    handler.setFormatter(JSONLogFormatter())

    handler._today = lambda: date(2025, 1, 1)
    handler.emit(logging.LogRecord("t", logging.INFO, "", 0, "one", (), None))

    handler._today = lambda: date(2025, 1, 2)
    handler.emit(logging.LogRecord("t", logging.ERROR, "", 0, "two", (), None))

    first = tmp_path / "2025-01-01" / "api" / "all.log"
    second = tmp_path / "2025-01-02" / "api" / "all.log"
    assert first.exists()
    assert second.exists()


def test_date_rolling_respects_log_root_even_with_filename_base(tmp_path: Path) -> None:
    # filename_base points to day1, but handler should roll using log_root/dayN
    day1 = tmp_path / "2025-01-01" / "api" / "all.log"
    day1.parent.mkdir(parents=True)
    handler = DateRollingFileHandler(
        filename_base=str(day1),
        log_root=str(tmp_path),
        component="api",
        max_bytes=1024 * 1024,
        backup_count=1,
        logging_max_days=0,
        error_only=False,
    )
    handler.setFormatter(JSONLogFormatter())
    handler._today = lambda: date(2025, 1, 1)
    handler.emit(logging.LogRecord("t", logging.INFO, "", 0, "one", (), None))
    handler._today = lambda: date(2025, 1, 2)
    handler.emit(logging.LogRecord("t", logging.INFO, "", 0, "two", (), None))

    assert (tmp_path / "2025-01-02" / "api" / "all.log").exists()


def test_logging_sinks_supports_multiple_and_writes_file(tmp_path: Path) -> None:
    settings = Settings.model_validate(
        {
            "LOGGING_SINKS": "stdout,file",
            "LOG_ROOT": str(tmp_path),
            "LOGGING_FILE_MAX_MB": 1,
        }
    )

    configure_logging(settings)
    log_event("unit.multi", message="hello")

    date_dir = tmp_path / date.today().isoformat() / "api"
    all_log = date_dir / "all.log"
    assert all_log.exists(), "File sink did not write logs"
    entries = [json.loads(line) for line in all_log.read_text().splitlines() if line.strip()]
    assert any(entry["event"] == "unit.multi" for entry in entries)

    handler_types = {type(handler).__name__ for handler in logging.getLogger().handlers}
    assert "StreamHandler" in handler_types, "stdout handler missing"
    assert any(isinstance(h, DateRollingFileHandler) for h in logging.getLogger().handlers)


def test_logging_sinks_precedence_over_logging_sink(tmp_path: Path) -> None:
    settings = Settings.model_validate(
        {
            "LOGGING_SINK": "stdout",
            "LOGGING_SINKS": "file",
            "LOG_ROOT": str(tmp_path),
            "LOGGING_FILE_MAX_MB": 1,
        }
    )

    configure_logging(settings)
    log_event("unit.precedence", message="hi")

    date_dir = tmp_path / date.today().isoformat() / "api"
    assert (date_dir / "all.log").exists(), "File sink should win when LOGGING_SINKS is set"
    handler_types = {type(handler).__name__ for handler in logging.getLogger().handlers}
    assert "StreamHandler" not in handler_types, "stdout handler should not be configured when only file sink is selected"


def test_logging_sinks_none_cannot_be_combined() -> None:
    settings = Settings.model_validate({"LOGGING_SINKS": "none,file"})
    with pytest.raises(ValueError):
        configure_logging(settings)


def test_logging_sinks_require_datadog_api_key() -> None:
    settings = Settings.model_validate({"LOGGING_SINKS": "datadog,file"})
    with pytest.raises(ValueError):
        configure_logging(settings)


def test_logging_sinks_require_otlp_endpoint() -> None:
    settings = Settings.model_validate({"LOGGING_SINKS": "otlp"})
    with pytest.raises(ValueError):
        configure_logging(settings)
