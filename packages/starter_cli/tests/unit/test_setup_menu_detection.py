from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pytest
from starter_cli.core import CLIContext
from starter_cli.workflows.setup_menu.detection import collect_setup_items


def _ctx(root: Path) -> CLIContext:
    ctx = CLIContext(project_root=root)
    ctx.loaded_env_files = []
    return ctx


def test_wizard_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path)
    items = collect_setup_items(ctx, stale_after=timedelta(days=7))
    wizard = _by_key(items, "wizard")
    assert wizard.status == "missing"
    assert wizard.progress == 0.0


def test_wizard_partial_and_progress(tmp_path: Path) -> None:
    reports = tmp_path / "var" / "reports"
    reports.mkdir(parents=True)
    summary = {
        "milestones": [
            {"milestone": "M1", "status": "ok"},
            {"milestone": "M2", "status": "pending"},
        ]
    }
    path = reports / "setup-summary.json"
    path.write_text(json.dumps(summary), encoding="utf-8")

    ctx = _ctx(tmp_path)
    items = collect_setup_items(ctx, stale_after=timedelta(days=7))
    wizard = _by_key(items, "wizard")
    assert wizard.status == "partial"
    assert wizard.progress and 0 < wizard.progress < 1
    assert wizard.progress_label == "1/2"


def test_stripe_levels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path)
    items = collect_setup_items(ctx, stale_after=timedelta(days=7))
    stripe = _by_key(items, "stripe")
    assert stripe.status == "missing"

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_123")
    items = collect_setup_items(ctx, stale_after=timedelta(days=7))
    stripe = _by_key(items, "stripe")
    assert stripe.status == "partial"

    monkeypatch.setenv("STRIPE_PRODUCT_PRICE_MAP", '{"starter":"price_123"}')
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_123")
    items = collect_setup_items(ctx, stale_after=timedelta(days=7))
    stripe = _by_key(items, "stripe")
    assert stripe.status == "done"


def test_geoip_optional(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path)
    monkeypatch.setenv("GEOIP_PROVIDER", "none")
    items = collect_setup_items(ctx, stale_after=timedelta(days=7))
    geoip = _by_key(items, "geoip")
    assert geoip.optional is True
    assert geoip.status == "missing"


def _by_key(items, key: str):
    for item in items:
        if item.key == key:
            return item
    raise AssertionError(f"setup item not found: {key}")
