from __future__ import annotations

from typing import cast

from starter_cli.core.context import build_context
from starter_cli.core.status_models import ProbeResult, ProbeState, ServiceStatus
from starter_cli.workflows.home import HomeController
from starter_cli.workflows.home import service as home_service
from starter_cli.workflows.home.doctor import DoctorRunner


def test_home_controller_summary(monkeypatch):
    ctx = build_context()
    controller = HomeController(ctx)

    def fake_collect():
        probes = [ProbeResult(name="env", state=ProbeState.OK, detail="ok")]
        services = [ServiceStatus(label="backend", state=ProbeState.OK, detail="running")]
        summary = {"ok": 1, "warn": 0, "error": 0, "skipped": 0}
        return probes, services, summary

    class FakeRunner:
        profile = "local"
        strict = False

        def collect(self):
            return fake_collect()

    monkeypatch.setattr(home_service, "DoctorRunner", lambda ctx, profile, strict: FakeRunner())
    result = controller.run(use_tui=False)
    assert result == 0


def test_home_shortcuts_include_setup():
    ctx = build_context()
    controller = HomeController(ctx)

    class DummyRunner:
        profile = "local"
        strict = False

    shortcuts = controller._build_shortcuts(cast(DoctorRunner, DummyRunner()))
    keys = {shortcut.key for shortcut in shortcuts}
    assert "S" in keys
