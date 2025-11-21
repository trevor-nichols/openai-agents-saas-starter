from __future__ import annotations

from starter_cli.core.context import build_context
from starter_cli.core.status_models import ProbeResult, ProbeState, ServiceStatus
from starter_cli.workflows.home import service as home_service
from starter_cli.workflows.home.service import HomeController


def test_home_controller_refresh_loop(monkeypatch):
    ctx = build_context()
    controller = HomeController(ctx)

    calls = {"count": 0}

    def fake_collect():
        calls["count"] += 1
        probes = [ProbeResult(name="env", state=ProbeState.OK, detail="ok")]
        services = [ServiceStatus(label="backend", state=ProbeState.OK, detail="running")]
        summary = {"ok": 1, "warn": 0, "error": 0, "skipped": 0}
        return probes, services, summary

    class FakeRunner:
        profile = "local"
        strict = False

        def collect(self):
            return fake_collect()

    class DummyLive:
        def __init__(self, *args, **kwargs):
            self.update_calls = 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def update(self, _layout):
            self.update_calls += 1
            if self.update_calls >= 2:
                raise SystemExit  # break the loop

    monkeypatch.setattr(home_service, "DoctorRunner", lambda ctx, profile, strict: FakeRunner())
    monkeypatch.setattr(home_service, "Live", lambda *args, **kwargs: DummyLive())
    # avoid sleep blocking
    monkeypatch.setattr(home_service.time, "sleep", lambda s: None)

    try:
        controller.run(use_tui=True)
    except SystemExit:
        pass

    assert calls["count"] >= 2
