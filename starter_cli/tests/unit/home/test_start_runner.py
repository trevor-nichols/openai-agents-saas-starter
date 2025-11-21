from __future__ import annotations

from types import SimpleNamespace

from starter_cli.core.context import build_context
from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home import start as start_mod
from starter_cli.workflows.home.start import StartRunner


class FakeProc(SimpleNamespace):
    def __init__(self, pid: int = 1234):
        super().__init__(pid=pid, stdout=None)
        self._poll = None

    def poll(self):
        return self._poll

def test_start_runner_handles_missing_command(monkeypatch):
    ctx = build_context()

    monkeypatch.setattr(start_mod.StartRunner, "_ports_available", lambda self: True)

    def fake_popen(*args, **kwargs):  # pragma: no cover - used in test
        raise FileNotFoundError("missing")

    monkeypatch.setattr(start_mod, "subprocess", SimpleNamespace(Popen=fake_popen))
    runner = StartRunner(ctx, target="backend", timeout=1, open_browser=False)
    assert runner.run() == 1


def test_start_runner_success_with_stubbed_health(monkeypatch):
    ctx = build_context()
    fake_proc = FakeProc()
    monkeypatch.setattr(start_mod.StartRunner, "_ports_available", lambda self: True)

    monkeypatch.setattr(
        start_mod,
        "subprocess",
        SimpleNamespace(Popen=lambda *args, **kwargs: fake_proc, PIPE="PIPE", STDOUT="STDOUT"),
    )

    ok_result = ProbeResult(name="api", state=ProbeState.OK, detail="ok")
    monkeypatch.setattr(start_mod, "api_probe", lambda: ok_result)
    monkeypatch.setattr(start_mod, "frontend_probe", lambda: ok_result)
    monkeypatch.setattr(start_mod.StartRunner, "_wait_for_processes", lambda self: 0)
    runner = StartRunner(ctx, target="dev", timeout=0.1, open_browser=False, skip_infra=True)
    assert runner.run() == 0


def test_start_runner_flapping_health(monkeypatch):
    ctx = build_context()
    fake_proc = FakeProc()
    monkeypatch.setattr(start_mod.StartRunner, "_ports_available", lambda self: True)
    monkeypatch.setattr(
        start_mod,
        "subprocess",
        SimpleNamespace(Popen=lambda *args, **kwargs: fake_proc, PIPE="PIPE", STDOUT="STDOUT"),
    )

    calls = {"api": 0}

    def api_probe_flap():
        calls["api"] += 1
        state = ProbeState.ERROR if calls["api"] == 1 else ProbeState.OK
        return ProbeResult(name="api", state=state, detail="flap")

    ok_result = ProbeResult(name="frontend", state=ProbeState.OK, detail="ok")
    monkeypatch.setattr(start_mod, "api_probe", api_probe_flap)
    monkeypatch.setattr(start_mod, "frontend_probe", lambda: ok_result)
    monkeypatch.setattr(start_mod.StartRunner, "_wait_for_processes", lambda self: 0)
    runner = StartRunner(ctx, target="backend", timeout=1.5, open_browser=False)
    assert runner.run() == 0


def test_frontend_port_guard_honors_app_public_url(monkeypatch):
    ctx = build_context()
    runner = StartRunner(ctx, target="frontend", timeout=0.1, open_browser=False)
    monkeypatch.setenv("APP_PUBLIC_URL", "http://localhost:4321")

    def fake_tcp_check(host, port, timeout):
        return (True, "busy") if port == 4321 else (False, "free")

    monkeypatch.setattr(start_mod, "tcp_check", fake_tcp_check)

    assert runner._ports_available() is False


def test_frontend_remote_app_public_url_keeps_local_port(monkeypatch):
    ctx = build_context()
    runner = StartRunner(ctx, target="frontend", timeout=0.1, open_browser=False)
    monkeypatch.setenv("APP_PUBLIC_URL", "https://myteam.ngrok.app")
    monkeypatch.delenv("PORT", raising=False)

    calls = []

    def fake_tcp_check(host, port, timeout):
        calls.append((host, port, timeout))
        return False, "free"

    monkeypatch.setattr(start_mod, "tcp_check", fake_tcp_check)

    assert runner._frontend_listen_port() == 3000
    assert runner._ports_available() is True
    assert calls == [("127.0.0.1", 3000, 0.5)]


def test_backend_env_strips_frontend_port(monkeypatch):
    ctx = build_context()
    runner = StartRunner(ctx, target="backend", timeout=0.1, open_browser=False)
    monkeypatch.setenv("PORT", "3000")
    env = runner._backend_env()
    assert "PORT" not in env
    assert env["ALEMBIC_CONFIG"].endswith("api-service/alembic.ini")


def test_frontend_env_sets_port_from_app_public_url(monkeypatch):
    ctx = build_context()
    runner = StartRunner(ctx, target="frontend", timeout=0.1, open_browser=False)
    monkeypatch.setenv("APP_PUBLIC_URL", "http://localhost:3100")
    env = runner._frontend_env()
    assert env["PORT"] == "3100"
    assert env["APP_PUBLIC_URL"].endswith(":3100")


def test_force_skips_stop_when_no_running(monkeypatch):
    ctx = build_context()
    runner = StartRunner(
        ctx, target="backend", timeout=0.1, open_browser=False, detach=True, force=True
    )

    dummy_state = object()
    status = SimpleNamespace(state="stopped", running=[], dead=[])

    monkeypatch.setattr(start_mod.stack_state, "load", lambda path: dummy_state)
    monkeypatch.setattr(start_mod.stack_state, "status", lambda s: status)

    called_stop = False
    called_clear = False

    def fake_stop(_state, **kwargs):
        nonlocal called_stop
        called_stop = True

    def fake_clear(_path):
        nonlocal called_clear
        called_clear = True

    monkeypatch.setattr(start_mod.stack_state, "stop_processes", fake_stop)
    monkeypatch.setattr(start_mod.stack_state, "clear", fake_clear)
    monkeypatch.setattr(start_mod.StartRunner, "_ports_available", lambda self: False)

    runner.run()

    assert called_stop is False
    assert called_clear is True
