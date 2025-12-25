from __future__ import annotations

import argparse
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast

import pytest
from starter_cli.commands import usage as usage_cmd
from starter_cli.services.usage import usage_ops
from starter_cli.core import CLIContext, CLIError
from starter_cli.workflows.usage import (
    PlanSyncResult,
    UsageEntitlementSyncResult,
    UsageReport,
    UsageReportArtifacts,
)
from starter_contracts.config import StarterSettingsProtocol


def _build_args(**overrides):
    defaults = {
        "path": None,
        "plan": None,
        "prune_missing": False,
        "dry_run": False,
        "allow_disabled_artifact": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def test_handle_sync_entitlements_invokes_workflow(monkeypatch, tmp_path):
    ctx = CLIContext(project_root=tmp_path)
    ctx.settings = cast(
        StarterSettingsProtocol,
        SimpleNamespace(database_url="sqlite:///test.db"),
    )

    artifact_dir = tmp_path / "var" / "reports"
    artifact_dir.mkdir(parents=True)
    artifact_path = artifact_dir / "usage-entitlements.json"
    artifact_path.write_text("{}", encoding="utf-8")

    captured = {}

    async def _fake_sync(**kwargs):
        captured.update(kwargs)
        return UsageEntitlementSyncResult(
            artifact_path=artifact_path,
            artifact_generated_at=None,
            artifact_enabled=True,
            dry_run=kwargs.get("dry_run", False),
            plan_results=[PlanSyncResult(plan_code="starter", inserted=1, updated=0, pruned=0)],
        )

    monkeypatch.setattr(usage_ops, "sync_usage_entitlements", _fake_sync)

    args = _build_args(
        plan=["starter"],
        prune_missing=True,
        dry_run=True,
        allow_disabled_artifact=True,
    )

    result = usage_cmd.handle_sync_entitlements(args, ctx)

    assert result == 0
    assert captured["plan_filter"] == ("starter",)
    assert captured["prune_missing"] is True
    assert captured["dry_run"] is True
    assert captured["allow_disabled_artifact"] is True


def test_handle_sync_entitlements_requires_artifact(tmp_path):
    ctx = CLIContext(project_root=tmp_path)
    ctx.settings = cast(
        StarterSettingsProtocol,
        SimpleNamespace(database_url="sqlite:///test.db"),
    )
    args = _build_args()
    with pytest.raises(CLIError):
        usage_cmd.handle_sync_entitlements(args, ctx)


def test_handle_export_report_generates_artifact(monkeypatch, tmp_path):
    ctx = CLIContext(project_root=tmp_path)
    ctx.settings = cast(
        StarterSettingsProtocol,
        SimpleNamespace(database_url="sqlite:///test.db"),
    )

    dummy_report = UsageReport(
        generated_at=datetime.now(UTC),
        applied_period_start=None,
        applied_period_end=None,
        tenant_filters=("acme",),
        plan_filters=("starter",),
        feature_filters=("messages",),
        warn_threshold=0.9,
        include_inactive=False,
        tenants=[],
    )

    captured_request = {}
    captured_paths = {}

    class _FakeService:
        async def generate_report(self, request):
            captured_request["request"] = request
            return dummy_report

    monkeypatch.setattr(usage_ops, "UsageReportService", lambda: _FakeService())

    def _fake_writer(report, *, json_path, csv_path):
        captured_paths["json"] = json_path
        captured_paths["csv"] = csv_path
        return UsageReportArtifacts(json_path=json_path, csv_path=csv_path)

    monkeypatch.setattr(usage_ops, "write_usage_report_files", _fake_writer)

    args = argparse.Namespace(
        period_start="2025-11-01T00:00:00Z",
        period_end=None,
        tenant=["acme", "acme"],
        plan=["starter"],
        feature=["messages"],
        include_inactive=False,
        warn_threshold=0.9,
        output_json=None,
        output_csv=None,
        no_json=False,
        no_csv=True,
    )

    result = usage_cmd.handle_export_report(args, ctx)

    assert result == 0
    request = captured_request["request"]
    assert request.tenant_slugs == ("acme",)
    assert request.plan_codes == ("starter",)
    assert captured_paths["json"].name == "usage-dashboard.json"
    assert captured_paths["csv"] is None


def test_handle_export_report_requires_artifact_enabled(tmp_path):
    ctx = CLIContext(project_root=tmp_path)
    ctx.settings = cast(
        StarterSettingsProtocol,
        SimpleNamespace(database_url="sqlite:///test.db"),
    )
    args = argparse.Namespace(
        period_start=None,
        period_end=None,
        tenant=None,
        plan=None,
        feature=None,
        include_inactive=False,
        warn_threshold=0.5,
        output_json=None,
        output_csv=None,
        no_json=True,
        no_csv=True,
    )
    with pytest.raises(CLIError):
        usage_cmd.handle_export_report(args, ctx)


def test_handle_export_report_validates_threshold(tmp_path):
    ctx = CLIContext(project_root=tmp_path)
    ctx.settings = cast(
        StarterSettingsProtocol,
        SimpleNamespace(database_url="sqlite:///test.db"),
    )
    args = argparse.Namespace(
        period_start=None,
        period_end=None,
        tenant=None,
        plan=None,
        feature=None,
        include_inactive=False,
        warn_threshold=1.2,
        output_json=None,
        output_csv=None,
        no_json=False,
        no_csv=False,
    )
    with pytest.raises(CLIError):
        usage_cmd.handle_export_report(args, ctx)
