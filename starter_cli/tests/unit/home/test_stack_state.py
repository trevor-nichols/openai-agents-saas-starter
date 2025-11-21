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
    # Simulate Windows where SIGKILL may be absent
    monkeypatch.delattr(stack_state.signal, "SIGKILL", raising=False)

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
