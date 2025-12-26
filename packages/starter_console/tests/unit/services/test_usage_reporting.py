from __future__ import annotations

import json
from pathlib import Path

from starter_console.services.usage.reporting import load_usage_report, load_usage_summary


def test_load_usage_summary(tmp_path: Path) -> None:
    report = {
        "generated_at": "2024-01-01T00:00:00Z",
        "tenant_count": 2,
        "feature_count": 2,
        "tenants": [
            {
                "tenant_slug": "acme",
                "features": [
                    {"feature_key": "tokens", "status": "approaching"},
                ],
            },
            {
                "tenant_slug": "beta",
                "features": [
                    {"feature_key": "images", "status": "ok"},
                ],
            },
        ],
    }
    path = tmp_path / "usage-dashboard.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    summary = load_usage_summary(path)

    assert summary is not None
    assert summary.tenant_count == 2
    assert summary.feature_count == 2
    assert summary.warning_count == 1


def test_load_usage_report_warnings(tmp_path: Path) -> None:
    report = {
        "generated_at": "2024-01-01T00:00:00Z",
        "tenant_count": 1,
        "feature_count": 2,
        "tenants": [
            {
                "tenant_slug": "acme",
                "features": [
                    {"feature_key": "tokens", "status": "approaching"},
                    {"feature_key": "images", "status": "hard_limit_exceeded"},
                ],
            },
        ],
    }
    path = tmp_path / "usage-dashboard.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    usage_report = load_usage_report(path)

    assert usage_report is not None
    warnings = usage_report.warnings
    assert len(warnings) == 2
    assert warnings[0].tenant_slug == "acme"
    assert warnings[0].feature_key == "tokens"
    assert warnings[0].status == "approaching"
