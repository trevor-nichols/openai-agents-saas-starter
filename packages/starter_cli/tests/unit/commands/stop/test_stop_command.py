from __future__ import annotations

import argparse
from types import SimpleNamespace

from starter_cli.core.context import build_context


def test_stop_command_no_state(tmp_path):
    ctx = build_context()
    import starter_cli.commands.stop as stop_mod

    pidfile = tmp_path / "stack.json"
    args = argparse.Namespace(pidfile=pidfile)

    # Should be a no-op when no stack is tracked
    assert stop_mod._handle_stop(args, ctx) == 0
    assert not pidfile.exists()


def test_stop_command_clears_state(tmp_path, monkeypatch):
    ctx = build_context()
    import starter_cli.commands.stop as stop_mod
    from starter_cli.services.infra import stack_ops
    stack_state = stack_ops.stack_state

    pidfile = tmp_path / "stack.json"
    state = stack_state.StackState(
        processes=[stack_state.StackProcess(label="backend", pid=0, command=["cmd"])],
        infra_started=False,
    )
    stack_state.save(state, pidfile)

    monkeypatch.setattr(stack_state, "stop_processes", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("COMPOSE_PROJECT_NAME", "test-project")
    args = argparse.Namespace(pidfile=pidfile)
    assert stop_mod._handle_stop(args, ctx) == 0
    assert not pidfile.exists()


def test_stop_runs_compose_down_with_env(tmp_path, monkeypatch):
    ctx = build_context()
    import starter_cli.commands.stop as stop_mod
    from starter_cli.services.infra import stack_ops
    stack_state = stack_ops.stack_state

    pidfile = tmp_path / "stack.json"
    state = stack_state.StackState(
        processes=[stack_state.StackProcess(label="backend", pid=0, command=["cmd"])],
        infra_started=True,
    )
    stack_state.save(state, pidfile)

    calls = {}

    def fake_run(cmd, cwd=None, env=None, check=None, stdout=None, stderr=None):
        calls["cmd"] = cmd
        calls["env"] = env
        return SimpleNamespace()

    tmp_project = tmp_path / "proj"
    tmp_project.mkdir()
    compose_file = tmp_project / "ops" / "compose" / "docker-compose.yml"
    compose_file.parent.mkdir(parents=True)
    compose_file.write_text("version: \"3.11\"\nservices: {}", encoding="utf-8")
    compose_env_path = tmp_project / ".env.compose"
    compose_env_path.write_text("COMPOSE_PROJECT_NAME=myproj\nFOO=bar\n", encoding="utf-8")

    monkeypatch.setattr(stack_state, "stop_processes", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(stack_state, "clear", lambda _path: None)
    monkeypatch.setattr(
        stack_state,
        "status",
        lambda _s: stack_state.StackStatus(
            state="running", running=[], dead=[], log_dir="", infra_started=True
        ),
    )
    monkeypatch.setenv("COMPOSE_PROJECT_NAME", "env-proj")

    monkeypatch.setattr(stack_ops.subprocess, "run", fake_run)
    monkeypatch.setattr(ctx, "project_root", tmp_project)

    args = argparse.Namespace(pidfile=pidfile)
    stop_mod._handle_stop(args, ctx)

    assert calls["cmd"] == ["docker", "compose", "-f", str(compose_file), "down"]
    assert calls["env"]["COMPOSE_PROJECT_NAME"] == "env-proj"  # env overrides file
    assert calls["env"]["COMPOSE_FILE"] == str(compose_file)
