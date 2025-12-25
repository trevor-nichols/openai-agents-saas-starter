from __future__ import annotations

import argparse
import io
import json

from starter_cli import app as cli_app
from starter_cli.commands import infra as infra_commands
from starter_cli.core import CLIContext
from starter_cli.ports.console import StdConsole
from starter_cli.services.infra import infra as infra_service


def _capture_console() -> tuple[io.StringIO, StdConsole]:
    buffer = io.StringIO()
    return buffer, StdConsole(stream=buffer, err_stream=buffer)


def test_infra_compose_runs_just(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, cwd, check):
        calls.append(cmd)
        class _Result:  # pragma: no cover - placeholder for subprocess.CompletedProcess
            pass

        return _Result()

    monkeypatch.setattr(infra_commands.subprocess, "run", fake_run)
    result = cli_app.main(["--skip-env", "infra", "compose", "up"])
    assert result == 0
    assert calls == [["just", "dev-up"]]


def test_infra_vault_runs_just(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, cwd, check):
        calls.append(cmd)
        class _Result:
            pass

        return _Result()

    monkeypatch.setattr(infra_commands.subprocess, "run", fake_run)
    result = cli_app.main(["--skip-env", "infra", "vault", "verify"])
    assert result == 0
    assert calls == [["just", "verify-vault"]]


def test_infra_deps_reports_missing_tools(monkeypatch) -> None:
    monkeypatch.setattr(
        infra_service,
        "detect_compose_command",
        lambda: ("/usr/bin/docker", "compose"),
    )

    def fake_which(binary: str) -> str | None:
        if binary == "pnpm":
            return None
        return f"/usr/bin/{binary}"

    monkeypatch.setattr(infra_service.shutil, "which", fake_which)
    statuses = {status.name: status for status in infra_service.collect_dependency_statuses()}
    assert statuses["Docker Engine"].status == "ok"
    assert statuses["Docker Compose"].status == "ok"
    assert statuses["pnpm"].status == "missing"


def test_infra_deps_json_missing(monkeypatch) -> None:
    buffer, console = _capture_console()
    statuses = [
        infra_service.DependencyStatus(
            name="Docker Engine",
            binaries=("docker",),
            command=("/usr/bin/docker",),
            hint="install docker",
            version="Docker version 28.0.0",
        ),
        infra_service.DependencyStatus(
            name="pnpm",
            binaries=("pnpm",),
            command=None,
            hint="Install via npm",
        ),
    ]
    monkeypatch.setattr(
        infra_commands,
        "collect_dependency_statuses",
        lambda: iter(statuses),
    )
    args = argparse.Namespace(format="json")
    result = infra_commands.handle_deps(args, CLIContext(console=console))
    payload = json.loads(buffer.getvalue())
    assert result == 1
    assert payload[0]["name"] == "Docker Engine"
    assert payload[1]["status"] == "missing"


def test_infra_deps_detects_missing_compose(monkeypatch) -> None:
    monkeypatch.setattr(infra_service, "detect_compose_command", lambda: None)

    def fake_which(binary: str) -> str | None:
        # everything else is installed
        return f"/usr/bin/{binary}"

    monkeypatch.setattr(infra_service.shutil, "which", fake_which)
    statuses = {status.name: status for status in infra_service.collect_dependency_statuses()}
    assert statuses["Docker Compose"].status == "missing"
