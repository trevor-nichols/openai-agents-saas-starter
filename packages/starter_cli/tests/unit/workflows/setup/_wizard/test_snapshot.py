from __future__ import annotations

from pathlib import Path

from starter_cli.adapters.env import EnvFile
from starter_cli.core import CLIContext
from starter_cli.workflows.setup._wizard.context import WizardContext
from starter_cli.workflows.setup._wizard.snapshot import build_diff, build_snapshot


def _build_context(tmp_path: Path) -> WizardContext:
    backend_env_path = tmp_path / "apps" / "api-service" / ".env.local"
    backend_env_path.parent.mkdir(parents=True, exist_ok=True)
    backend_env_path.write_text("", encoding="utf-8")
    frontend_env_path = tmp_path / "apps" / "web-app" / ".env.local"
    frontend_env_path.parent.mkdir(parents=True, exist_ok=True)
    frontend_env_path.write_text("", encoding="utf-8")
    ctx = CLIContext(project_root=tmp_path, env_files=(backend_env_path,))
    return WizardContext(
        cli_ctx=ctx,
        profile="demo",
        backend_env=EnvFile(backend_env_path),
        frontend_env=EnvFile(frontend_env_path),
        frontend_path=frontend_env_path,
    )


def test_snapshot_and_diff_capture_changes(tmp_path: Path) -> None:
    context = _build_context(tmp_path)
    context.hosting_preset = "local_docker"
    context.show_advanced_prompts = False

    context.set_backend("ENVIRONMENT", "development")
    context.set_backend("OPENAI_API_KEY", "sk-test", mask=True)
    context.set_frontend("PLAYWRIGHT_BASE_URL", "http://localhost:3000")

    snapshot_one = build_snapshot(context)
    assert snapshot_one["metadata"]["hosting_preset"] == "local_docker"
    assert snapshot_one["backend_env"]["OPENAI_API_KEY"]["set"] is True
    assert snapshot_one["backend_env"]["OPENAI_API_KEY"]["hash"] != "sk-test"

    context.set_backend("OPENAI_API_KEY", "sk-test-2", mask=True)
    context.set_backend_bool("ENABLE_BILLING", True)

    snapshot_two = build_snapshot(context)
    diff = build_diff(snapshot_one, snapshot_two)
    assert "OPENAI_API_KEY" in diff["backend_env"]["changed"]
    assert "ENABLE_BILLING" in diff["backend_env"]["added"]
