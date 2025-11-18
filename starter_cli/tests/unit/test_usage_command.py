from __future__ import annotations

import argparse
from types import SimpleNamespace
from typing import cast

import pytest
from starter_cli.commands import usage as usage_cmd
from starter_cli.core import CLIContext, CLIError
from starter_cli.workflows.usage import PlanSyncResult, UsageEntitlementSyncResult
from starter_shared.config import StarterSettingsProtocol


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

    monkeypatch.setattr(usage_cmd, "sync_usage_entitlements", _fake_sync)

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
