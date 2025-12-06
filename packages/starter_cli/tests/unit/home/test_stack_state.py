from __future__ import annotations

from starter_cli.workflows.home import stack_state


def test_stack_state_roundtrip(tmp_path):
    path = tmp_path / "stack.json"
    state = stack_state.StackState(
        processes=[stack_state.StackProcess(label="backend", pid=123, command=["hatch", "run"])],
        log_dir="/tmp/logs",
        infra_started=True,
    )

    stack_state.save(state, path)
    loaded = stack_state.load(path)

    assert loaded is not None
    assert loaded.infra_started is True
    assert len(loaded.processes) == 1
    assert loaded.processes[0].label == "backend"


def test_status_degraded(monkeypatch):
    state = stack_state.StackState(
        processes=[
            stack_state.StackProcess(label="backend", pid=1, command=["a"]),
            stack_state.StackProcess(label="frontend", pid=2, command=["b"]),
        ]
    )

    monkeypatch.setattr(stack_state, "is_alive", lambda pid: pid == 1)

    summary = stack_state.status(state)

    assert summary.state == "degraded"
    assert len(summary.running) == 1
    assert len(summary.dead) == 1


def test_stop_processes_fallback_without_sigkill(monkeypatch):
    # Simulate Windows where SIGKILL may be absent and killpg unavailable
    monkeypatch.delattr(stack_state.signal, "SIGKILL", raising=False)
    monkeypatch.delattr(stack_state.os, "killpg", raising=False)
    monkeypatch.delattr(stack_state.os, "getpgid", raising=False)

    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(stack_state.os, "kill", lambda pid, sig: calls.append((pid, sig)))
    monkeypatch.setattr(stack_state, "is_alive", lambda pid: True)
    monkeypatch.setattr(stack_state.time, "time", lambda: 0)
    monkeypatch.setattr(stack_state.time, "sleep", lambda _secs: None)

    state = stack_state.StackState(
        processes=[stack_state.StackProcess(label="backend", pid=1, command=["run"])],
    )

    stack_state.stop_processes(state, grace_seconds=0)

    # Two calls: initial SIGTERM, fallback SIGTERM (since SIGKILL missing)
    assert calls == [(1, stack_state.signal.SIGTERM), (1, stack_state.signal.SIGTERM)]


def test_stop_processes_prefers_process_group(monkeypatch):
    # Ensure we target the whole process group (pnpm/node, uvicorn reloaders)
    pg_calls: list[tuple[int, int]] = []
    kill_calls: list[tuple[int, int]] = []

    monkeypatch.setattr(stack_state.os, "killpg", lambda pgid, sig: pg_calls.append((pgid, sig)))
    monkeypatch.setattr(stack_state.os, "getpgid", lambda pid: pid + 100)
    monkeypatch.setattr(stack_state.os, "kill", lambda pid, sig: kill_calls.append((pid, sig)))
    monkeypatch.setattr(stack_state.signal, "SIGKILL", stack_state.signal.SIGKILL)
    monkeypatch.setattr(stack_state.time, "time", lambda: 0)
    monkeypatch.setattr(stack_state.time, "sleep", lambda _secs: None)
    monkeypatch.setattr(stack_state, "is_alive", lambda pid: True)

    state = stack_state.StackState(
        processes=[stack_state.StackProcess(label="frontend", pid=5, command=["pnpm", "dev"])],
    )

    stack_state.stop_processes(state, grace_seconds=0)

    # Should signal the group both times; no direct pid kill when killpg succeeds
    assert pg_calls == [(105, stack_state.signal.SIGTERM), (105, stack_state.signal.SIGKILL)]
    assert kill_calls == []
