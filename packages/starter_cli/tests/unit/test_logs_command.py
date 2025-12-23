from __future__ import annotations

import argparse
import io
from pathlib import Path

import pytest
from starter_cli.commands import logs as logs_cmd
from starter_cli.core.context import CLIContext
from starter_cli.ports.console import ConsolePort, StdConsole


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid cached Starter settings interfering with env-driven tests."""

    monkeypatch.setattr(logs_cmd.CLIContext, "optional_settings", lambda self: None)


def _ctx(tmp_path: Path, console: ConsolePort | None = None) -> CLIContext:
    return CLIContext(project_root=tmp_path, console=console or StdConsole())


class CaptureConsole(StdConsole):
    def __init__(self) -> None:
        buffer = io.StringIO()
        super().__init__(stream=buffer, err_stream=buffer)
        self.messages: list[str] = []

    def info(self, msg: str, topic: str | None = None, stream=None) -> None:
        self.messages.append(msg)

    def warn(self, msg: str, topic: str | None = None, stream=None) -> None:
        self.messages.append(msg)


def test_plan_targets_includes_api_tail_and_compose(monkeypatch, tmp_path: Path) -> None:
    log_file = tmp_path / "api.log"
    log_file.write_text("hi")

    monkeypatch.setenv("LOGGING_SINK", "file")
    monkeypatch.setenv("LOGGING_FILE_PATH", str(log_file))
    monkeypatch.setenv("ENABLE_OTEL_COLLECTOR", "true")
    monkeypatch.setenv("ENABLE_FRONTEND_LOG_INGEST", "true")

    monkeypatch.setattr(logs_cmd, "_detect_compose_command", lambda: ["docker", "compose"])

    ctx = _ctx(tmp_path)
    targets, notes = logs_cmd._plan_targets(
        ctx, ["all"], lines=50, follow=True, errors_only=False, console=ctx.console
    )

    names = {t.name for t in targets}
    assert {"api", "postgres", "redis", "collector"}.issubset(names)

    api = next(t for t in targets if t.name == "api")
    assert "-f" in api.command  # follow flag inserted
    assert str(log_file) in api.command

    assert any("Frontend logs flow" in note for level, note in notes)


def test_plan_targets_warns_when_no_file_sink(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("LOGGING_SINK", raising=False)
    monkeypatch.delenv("LOGGING_FILE_PATH", raising=False)
    monkeypatch.setattr(logs_cmd, "_detect_compose_command", lambda: None)

    ctx = _ctx(tmp_path)
    targets, notes = logs_cmd._plan_targets(
        ctx, ["api"], lines=10, follow=False, errors_only=False, console=ctx.console
    )

    assert not any(t.name == "api" for t in targets)
    assert any("not writing to a file" in note for level, note in notes)


def test_normalize_services_skips_collector_when_disabled(monkeypatch) -> None:
    capture_console = CaptureConsole()
    normalized = logs_cmd._normalize_services(
        ["collector"],
        enable_collector=False,
        console=capture_console,
    )

    assert "collector" not in normalized
    assert capture_console.messages  # warning emitted


def test_resolves_api_error_log_from_dated_layout(monkeypatch, tmp_path: Path) -> None:
    base = tmp_path / "var" / "log"
    date_root = base / "2025-01-01" / "api"
    date_root.mkdir(parents=True)
    err_log = date_root / "error.log"
    err_log.write_text("oops")

    monkeypatch.setenv("LOG_ROOT", str(base))
    monkeypatch.setenv("LOGGING_SINK", "file")

    ctx = _ctx(tmp_path)
    targets, _ = logs_cmd._plan_targets(
        ctx, ["api"], lines=5, follow=False, errors_only=True, console=ctx.console
    )

    assert any(str(err_log) in " ".join(t.command) for t in targets)


def test_duplex_error_log_tail_when_stdout_sink(monkeypatch, tmp_path: Path) -> None:
    base = tmp_path / "var" / "log"
    date_root = base / "2025-01-01" / "api"
    date_root.mkdir(parents=True)
    err_log = date_root / "error.log"
    err_log.write_text("stderr only")

    monkeypatch.setenv("LOG_ROOT", str(base))
    monkeypatch.setenv("LOGGING_SINK", "stdout")

    ctx = _ctx(tmp_path)
    targets, notes = logs_cmd._plan_targets(
        ctx, ["api"], lines=10, follow=False, errors_only=True, console=ctx.console
    )

    assert any(str(err_log) in " ".join(t.command) for t in targets)
    assert not any("not writing to a file sink" in note for _level, note in notes)


def test_archive_dry_run(monkeypatch, tmp_path: Path) -> None:
    base = tmp_path / "var" / "log"
    old = base / "2024-01-01"
    old.mkdir(parents=True)
    (old / "api").mkdir(parents=True)
    capture_console = CaptureConsole()
    ctx = _ctx(tmp_path, console=capture_console)
    args = argparse.Namespace(days=300, log_root=None, dry_run=True)

    msgs: list[str] = []

    logs_cmd._handle_archive(args, ctx)
    msgs.extend(capture_console.messages)

    assert any("would archive" in msg for msg in msgs)


def test_resolve_tail_settings_defaults() -> None:
    args = argparse.Namespace(lines=None, follow=False, no_follow=False)
    lines, follow = logs_cmd._resolve_tail_settings(args)
    assert lines == logs_cmd.DEFAULT_LINES
    assert follow is True


def test_resolve_tail_settings_lines_disable_follow() -> None:
    args = argparse.Namespace(lines=5, follow=False, no_follow=False)
    lines, follow = logs_cmd._resolve_tail_settings(args)
    assert lines == 5
    assert follow is False


def test_resolve_tail_settings_follow_override() -> None:
    args = argparse.Namespace(lines=5, follow=True, no_follow=False)
    lines, follow = logs_cmd._resolve_tail_settings(args)
    assert lines == 5
    assert follow is True
