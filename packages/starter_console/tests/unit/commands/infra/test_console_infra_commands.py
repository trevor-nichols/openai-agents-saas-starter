from __future__ import annotations

import argparse
import io
import json

import pytest

from starter_console import app as cli_app
from starter_console.commands import infra as infra_commands
from starter_console.core import CLIContext, CLIError
from starter_console.ports.console import StdConsole
from starter_console.services.infra import infra as infra_service


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


def test_infra_terraform_export_writes_file(tmp_path) -> None:
    output_path = tmp_path / "terraform.tfvars"
    buffer, console = _capture_console()
    ctx = CLIContext(project_root=tmp_path, console=console)
    args = argparse.Namespace(
        provider="aws",
        mode="template",
        format="hcl",
        output=str(output_path),
        answers_file=None,
        var=None,
        extra_var=None,
        env_file=None,
        include_advanced=False,
        include_secrets=False,
        include_defaults=False,
    )

    result = infra_commands.handle_terraform_export(args, ctx)

    assert result == 0
    assert output_path.exists()
    contents = output_path.read_text(encoding="utf-8")
    assert "project_name" in contents


def _aws_answers_payload(*, include_typo: bool) -> dict[str, str]:
    payload = {
        "PROJECT_NAME": "starter",
        "ENVIRONMENT": "prod",
        "API_IMAGE": "example.com/api:latest",
        "WEB_IMAGE": "example.com/web:latest",
        "DB_PASSWORD": "super-secret",
        "STORAGE_BUCKET_NAME": "starter-assets",
        "API_SECRETS": json.dumps({"DATABASE_URL": "db-secret", "REDIS_URL": "redis-secret"}),
        "ENABLE_HTTPS": "false",
        "REDIS_REQUIRE_AUTH_TOKEN": "false",
        "SECRETS_PROVIDER": "aws_sm",
        "AWS_SM_SIGNING_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123:secret:sign",
        "AUTH_KEY_SECRET_NAME": "auth-key",
    }
    if include_typo:
        payload["STORAGE_BUKET_NAME"] = "typo-assets"
    return payload


def test_terraform_export_filled_rejects_suspicious_answers_key(tmp_path) -> None:
    answers_path = tmp_path / "answers.json"
    answers_path.write_text(
        json.dumps(_aws_answers_payload(include_typo=True)),
        encoding="utf-8",
    )
    ctx = CLIContext(project_root=tmp_path, console=StdConsole(stream=io.StringIO()))
    args = argparse.Namespace(
        provider="aws",
        mode="filled",
        format="hcl",
        output=str(tmp_path / "terraform.tfvars"),
        answers_file=[str(answers_path)],
        var=None,
        extra_var=None,
        env_file=None,
        include_advanced=False,
        include_secrets=False,
        include_defaults=False,
    )

    with pytest.raises(CLIError, match="Suspicious Terraform inputs detected in answers file"):
        infra_commands.handle_terraform_export(args, ctx)


def test_terraform_export_template_warns_on_suspicious_answers_key(tmp_path) -> None:
    answers_path = tmp_path / "answers.json"
    answers_path.write_text(
        json.dumps(_aws_answers_payload(include_typo=True)),
        encoding="utf-8",
    )
    buffer, console = _capture_console()
    ctx = CLIContext(project_root=tmp_path, console=console)
    args = argparse.Namespace(
        provider="aws",
        mode="template",
        format="hcl",
        output=str(tmp_path / "terraform.tfvars"),
        answers_file=[str(answers_path)],
        var=None,
        extra_var=None,
        env_file=None,
        include_advanced=False,
        include_secrets=False,
        include_defaults=False,
    )

    result = infra_commands.handle_terraform_export(args, ctx)

    assert result == 0
    assert "Suspicious Terraform inputs detected in answers file" in buffer.getvalue()
