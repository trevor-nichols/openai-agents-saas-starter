from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from starter_cli.core import CLIContext, CLIError
from starter_cli.services.infra import backend_scripts
from starter_cli.services.infra.backend_scripts import extract_json_payload


def test_extract_json_payload_reads_last_valid_line() -> None:
    stdout = "noise\n{\"ok\": false}\n{\"result\": \"done\"}\n"
    payload = extract_json_payload(stdout, required_keys=["result"])
    assert payload["result"] == "done"


def test_extract_json_payload_requires_keys() -> None:
    with pytest.raises(CLIError):
        extract_json_payload("{\"ok\": true}", required_keys=["result"])


def test_run_backend_script_env_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path
    backend_root = project_root / "apps" / "api-service"
    script_dir = backend_root / "scripts"
    script_dir.mkdir(parents=True)
    (script_dir / "dummy.py").write_text("# noop\n", encoding="utf-8")

    default_env = tmp_path / "default.env"
    custom_env = tmp_path / "custom.env"
    default_env.write_text("FOO=from_default\nBAR=from_default\n", encoding="utf-8")
    custom_env.write_text("FOO=from_custom\nBAR=from_custom\n", encoding="utf-8")

    monkeypatch.setattr(backend_scripts, "DEFAULT_ENV_FILES", (default_env,))
    monkeypatch.setenv("FOO", "from_os")

    ctx = CLIContext(project_root=project_root, env_files=(default_env, custom_env))
    ctx.loaded_env_files = [default_env, custom_env]

    captured: dict[str, object] = {}

    def _run(cmd, *, cwd, env, text, capture_output, check):
        captured["env"] = env
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(backend_scripts.subprocess, "run", _run)

    backend_scripts.run_backend_script(
        project_root=project_root,
        script_name="dummy.py",
        args=[],
        env_overrides={"FOO": "from_override"},
        ctx=ctx,
    )

    env = captured["env"]
    assert isinstance(env, dict)
    assert env["FOO"] == "from_override"
    assert env["BAR"] == "from_custom"


def test_run_backend_script_skips_default_env_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path
    backend_root = project_root / "apps" / "api-service"
    script_dir = backend_root / "scripts"
    script_dir.mkdir(parents=True)
    (script_dir / "dummy.py").write_text("# noop\n", encoding="utf-8")

    default_env = tmp_path / "default.env"
    custom_env = tmp_path / "custom.env"
    default_env.write_text("DEFAULT_ONLY=1\n", encoding="utf-8")
    custom_env.write_text("CUSTOM_ONLY=2\n", encoding="utf-8")

    monkeypatch.setattr(backend_scripts, "DEFAULT_ENV_FILES", (default_env,))
    monkeypatch.delenv("DEFAULT_ONLY", raising=False)
    monkeypatch.delenv("CUSTOM_ONLY", raising=False)

    ctx = CLIContext(
        project_root=project_root,
        env_files=(default_env, custom_env),
        skip_env=True,
    )
    ctx.loaded_env_files = [default_env, custom_env]

    captured: dict[str, object] = {}

    def _run(cmd, *, cwd, env, text, capture_output, check):
        captured["env"] = env
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(backend_scripts.subprocess, "run", _run)

    backend_scripts.run_backend_script(
        project_root=project_root,
        script_name="dummy.py",
        args=[],
        ctx=ctx,
    )

    env = captured["env"]
    assert isinstance(env, dict)
    assert "DEFAULT_ONLY" not in env
    assert env["CUSTOM_ONLY"] == "2"
