from __future__ import annotations

from starter_cli.core.context import build_context
from starter_cli.core.status_models import ProbeResult, ProbeState, ServiceStatus
from starter_cli.workflows.home import HomeController
from starter_cli.workflows.home import service as home_service


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

