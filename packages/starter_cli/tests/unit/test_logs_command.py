from __future__ import annotations

from pathlib import Path

import pytest
from starter_cli.commands import logs as logs_cmd
from starter_cli.core.context import CLIContext


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid cached Starter settings interfering with env-driven tests."""

    monkeypatch.setattr(logs_cmd.CLIContext, "optional_settings", lambda self: None)


def _ctx(tmp_path: Path) -> CLIContext:
    return CLIContext(project_root=tmp_path)


def test_plan_targets_includes_api_tail_and_compose(monkeypatch, tmp_path: Path) -> None:
    log_file = tmp_path / "api.log"
    log_file.write_text("hi")

    monkeypatch.setenv("LOGGING_SINK", "file")
    monkeypatch.setenv("LOGGING_FILE_PATH", str(log_file))
    monkeypatch.setenv("ENABLE_OTEL_COLLECTOR", "true")
    monkeypatch.setenv("ENABLE_FRONTEND_LOG_INGEST", "true")

    monkeypatch.setattr(logs_cmd, "_detect_compose_command", lambda: ["docker", "compose"])

    targets, notes = logs_cmd._plan_targets(_ctx(tmp_path), ["all"], lines=50, follow=True)

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

    targets, notes = logs_cmd._plan_targets(_ctx(tmp_path), ["api"], lines=10, follow=False)

    assert not any(t.name == "api" for t in targets)
    assert any("not writing to a file" in note for level, note in notes)


def test_normalize_services_skips_collector_when_disabled(monkeypatch) -> None:
    called = []

    def fake_warn(msg: str, topic: str | None = None, stream=None) -> None:
        called.append(msg)

    monkeypatch.setattr(logs_cmd.console, "warn", fake_warn)
    normalized = logs_cmd._normalize_services(["collector"], enable_collector=False)

    assert "collector" not in normalized
    assert called  # warning emitted
