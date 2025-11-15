from __future__ import annotations

import io
import json

from starter_cli.cli import infra_commands
from starter_cli.cli import main as cli_main
from starter_cli.cli.console import console as cli_console


def test_infra_compose_runs_make(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, cwd, check):
        calls.append(cmd)
        class _Result:  # pragma: no cover - placeholder for subprocess.CompletedProcess
            pass

        return _Result()

    monkeypatch.setattr(infra_commands.subprocess, "run", fake_run)
    result = cli_main.main(["--skip-env", "infra", "compose", "up"])
    assert result == 0
    assert calls == [["make", "dev-up"]]


def test_infra_vault_runs_make(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, cwd, check):
        calls.append(cmd)
        class _Result:
            pass

        return _Result()

    monkeypatch.setattr(infra_commands.subprocess, "run", fake_run)
    result = cli_main.main(["--skip-env", "infra", "vault", "verify"])
    assert result == 0
    assert calls == [["make", "verify-vault"]]


def test_infra_deps_reports_missing_tools(monkeypatch) -> None:
    buffer = io.StringIO()
    monkeypatch.setattr(cli_console, "stream", buffer)
    monkeypatch.setattr(cli_console, "err_stream", buffer)
    monkeypatch.setattr(
        infra_commands,
        "_detect_compose_binary",
        lambda: "/usr/bin/docker compose",
    )

    def fake_which(binary: str) -> str | None:
        if binary == "pnpm":
            return None
        return f"/usr/bin/{binary}"

    monkeypatch.setattr(infra_commands.shutil, "which", fake_which)
    result = cli_main.main(["--skip-env", "infra", "deps"])
    assert result == 0
    output = buffer.getvalue()
    assert "Docker Engine" in output
    assert "pnpm: missing" in output


def test_infra_deps_json_missing(monkeypatch) -> None:
    buffer = io.StringIO()
    monkeypatch.setattr(cli_console, "stream", buffer)
    monkeypatch.setattr(cli_console, "err_stream", buffer)
    monkeypatch.setattr(
        infra_commands,
        "_detect_compose_binary",
        lambda: "/usr/bin/docker compose",
    )

    def fake_which(binary: str) -> str | None:
        if binary == "pnpm":
            return None
        return f"/usr/bin/{binary}"

    monkeypatch.setattr(infra_commands.shutil, "which", fake_which)
    result = cli_main.main(["--skip-env", "infra", "deps", "--format", "json"])
    payload = json.loads(buffer.getvalue())
    assert result == 1
    pnpm_entry = next(entry for entry in payload if entry["name"] == "pnpm")
    assert pnpm_entry["status"] == "missing"


def test_infra_deps_detects_missing_compose(monkeypatch) -> None:
    buffer = io.StringIO()
    monkeypatch.setattr(cli_console, "stream", buffer)
    monkeypatch.setattr(cli_console, "err_stream", buffer)

    monkeypatch.setattr(infra_commands, "_detect_compose_binary", lambda: None)

    def fake_which(binary: str) -> str | None:
        # everything else is installed
        return f"/usr/bin/{binary}"

    monkeypatch.setattr(infra_commands.shutil, "which", fake_which)
    result = cli_main.main(["--skip-env", "infra", "deps"])
    assert result == 0
    output = buffer.getvalue()
    assert "Docker Compose v2: missing" in output
