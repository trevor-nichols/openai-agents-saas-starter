from __future__ import annotations

from datetime import UTC, datetime

from starter_cli.core.status_models import ProbeResult, ProbeState, ServiceStatus
from starter_cli.ui import view_models
from starter_cli.workflows.setup_menu.models import SetupItem


def test_status_label_uppercase() -> None:
    assert view_models.status_label(ProbeState.OK) == "OK"
    assert view_models.status_label(ProbeState.ERROR) == "ERROR"


def test_probe_rows_sorted_by_severity() -> None:
    probes = [
        ProbeResult(name="alpha", state=ProbeState.OK),
        ProbeResult(name="beta", state=ProbeState.ERROR),
        ProbeResult(name="gamma", state=ProbeState.WARN),
    ]

    rows = view_models.probe_rows(probes)

    assert [row[0] for row in rows] == ["beta", "gamma", "alpha"]


def test_service_rows_include_endpoints() -> None:
    services = [
        ServiceStatus(label="api", state=ProbeState.OK, detail="ready"),
        ServiceStatus(
            label="frontend",
            state=ProbeState.WARN,
            detail="degraded",
            endpoints=("http://localhost:3000",),
        ),
    ]

    rows = view_models.service_rows(services)

    assert rows[0][2] == "ready"
    assert "localhost:3000" in rows[1][2]


def test_setup_row_optional_and_progress() -> None:
    item = SetupItem(
        key="demo",
        label="Demo Token",
        status="missing",
        detail="Missing",
        optional=True,
        progress=0.25,
    )

    row = view_models.setup_row(item)

    assert row[0] == "MISSING"
    assert row[2].endswith("(optional)")
    assert row[3] == "25%"


def test_format_summary_includes_stack_state() -> None:
    summary = {"ok": 2, "warn": 1, "error": 0, "skipped": 0}

    label = view_models.format_summary(
        summary,
        profile="local",
        strict=False,
        stack_state="running",
    )

    assert "Profile: local" in label
    assert "Stack: running" in label
    assert "ok=2" in label


def test_format_timestamp_iso() -> None:
    value = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)

    assert view_models.format_timestamp(value) == "2024-01-02T03:04:05+00:00"
