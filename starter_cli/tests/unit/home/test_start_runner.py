from __future__ import annotations

from types import SimpleNamespace

import pytest

from starter_cli.core.context import build_context
from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home import start as start_mod
from starter_cli.workflows.home.start import StartRunner


class FakeProc(SimpleNamespace):
    def __init__(self, pid: int = 1234):
        super().__init__(pid=pid)


def test_start_runner_handles_missing_command(monkeypatch):
    ctx = build_context()

    def fake_popen(*args, **kwargs):  # pragma: no cover - used in test
        raise FileNotFoundError("missing")

    monkeypatch.setattr(start_mod, "subprocess", SimpleNamespace(Popen=fake_popen))
    runner = StartRunner(ctx, target="backend", timeout=1, open_browser=False)
    assert runner.run() == 1


def test_start_runner_success_with_stubbed_health(monkeypatch):
    ctx = build_context()
    fake_proc = FakeProc()

    monkeypatch.setattr(
        start_mod,
        "subprocess",
        SimpleNamespace(Popen=lambda *args, **kwargs: fake_proc),
    )

    ok_result = ProbeResult(name="api", state=ProbeState.OK, detail="ok")
    monkeypatch.setattr(start_mod, "api_probe", lambda: ok_result)
    monkeypatch.setattr(start_mod, "frontend_probe", lambda: ok_result)
    runner = StartRunner(ctx, target="dev", timeout=0.1, open_browser=False, skip_infra=True)
    assert runner.run() == 0

