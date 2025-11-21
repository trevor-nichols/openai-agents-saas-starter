from __future__ import annotations

from starter_cli.core.context import build_context
from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home import doctor as doctor_mod
from starter_cli.workflows.home.probes.registry import ProbeSpec


def test_expect_flags_skip_probes(monkeypatch):
    def fake_probe(ctx):
        return ProbeResult(name="api", state=ProbeState.ERROR, detail="boom")

    monkeypatch.setattr(
        doctor_mod,
        "PROBE_SPECS",
        (
            ProbeSpec(name="api", factory=lambda ctx: fake_probe(ctx), category="core"),
        ),
    )
    env = {"EXPECT_API_DOWN": "true"}
    monkeypatch.setenv("EXPECT_API_DOWN", "true")
    runner = doctor_mod.DoctorRunner(build_context(), profile="local", strict=False)
    probes = runner._run_probes()
    assert probes[0].state is ProbeState.SKIPPED
    assert "suppressed" in (probes[0].detail or "")
