from __future__ import annotations

from starter_cli.core.context import build_context
from starter_cli.core.status_models import ProbeResult, ProbeState, ServiceStatus
from starter_cli.services.hub import HubService
from starter_cli.services import hub as hub_service


def test_hub_service_load_home(monkeypatch):
    ctx = build_context()
    hub = HubService(ctx)

    probes = [ProbeResult(name="env", state=ProbeState.OK, detail="ok")]
    services = [ServiceStatus(label="backend", state=ProbeState.OK, detail="running")]
    summary = {"ok": 1, "warn": 0, "error": 0, "skipped": 0}

    class FakeRunner:
        profile = "demo"
        strict = False

        def collect(self):
            return probes, services, summary

    monkeypatch.setattr(hub_service, "DoctorRunner", lambda ctx, profile, strict: FakeRunner())
    snapshot = hub.load_home(profile="demo", strict=False)
    assert snapshot.summary == summary
    assert snapshot.profile == "demo"
