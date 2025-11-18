from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext, CLIError
from starter_cli.workflows.usage import (
    EntitlementLoaderError,
    PlanSyncResult,
    UsageEntitlementSyncResult,
    sync_usage_entitlements,
)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    usage_parser = subparsers.add_parser("usage", help="Usage guardrail utilities.")
    usage_subparsers = usage_parser.add_subparsers(dest="usage_command")

    sync_parser = usage_subparsers.add_parser(
        "sync-entitlements",
        help="Upsert billing plan features from var/reports/usage-entitlements.json.",
    )
    sync_parser.add_argument(
        "--path",
        metavar="PATH",
        help=(
            "Override the entitlements artifact path (defaults to "
            "var/reports/usage-entitlements.json)."
        ),
    )
    sync_parser.add_argument(
        "--plan",
        action="append",
        metavar="CODE",
        help="Limit syncing to one or more plan codes (repeatable).",
    )
    sync_parser.add_argument(
        "--prune-missing",
        action="store_true",
        help="Delete plan features that are no longer present in the artifact.",
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview inserts/updates/deletes without modifying the database.",
    )
    sync_parser.add_argument(
        "--allow-disabled-artifact",
        action="store_true",
        help="Process the artifact even when ENABLE_USAGE_GUARDRAILS was false during generation.",
    )
    sync_parser.set_defaults(handler=handle_sync_entitlements)


def handle_sync_entitlements(args: argparse.Namespace, ctx: CLIContext) -> int:
    settings = ctx.require_settings()
    database_url = getattr(settings, "database_url", None)
    if not database_url:
        raise CLIError(
            "DATABASE_URL is not configured; run the wizard or pass --env-file to load it."
        )

    artifact_path = _resolve_artifact_path(ctx, args.path)
    plan_filter = tuple(args.plan) if args.plan else None

    try:
        result = asyncio.run(
            sync_usage_entitlements(
                database_url=database_url,
                artifact_path=artifact_path,
                plan_filter=plan_filter,
                prune_missing=args.prune_missing,
                dry_run=args.dry_run,
                allow_disabled_artifact=args.allow_disabled_artifact,
            )
        )
    except EntitlementLoaderError as exc:
        raise CLIError(str(exc)) from exc

    _render_summary(result)
    if result.dry_run:
        console.warn(
            "Dry-run complete. Re-run without --dry-run to apply changes.",
            topic="usage",
        )
    else:
        console.success(
            f"Synced usage entitlements for {result.plans_processed} plan(s).",
            topic="usage",
        )
    return 0


def _resolve_artifact_path(ctx: CLIContext, override: str | None) -> Path:
    if override:
        path = Path(override).expanduser().resolve()
    else:
        path = ctx.project_root / "var" / "reports" / "usage-entitlements.json"
    if not path.exists():
        raise CLIError(f"Entitlement artifact not found at {path}.")
    return path


def _render_summary(result: UsageEntitlementSyncResult) -> None:
    console.info(
        f"Artifact: {result.artifact_path} (enabled={result.artifact_enabled})",
        topic="usage",
    )
    for plan_result in result.plan_results:
        console.info(
            _format_plan_summary(plan_result),
            topic="usage",
        )


def _format_plan_summary(plan_result: PlanSyncResult) -> str:
    return (
        f"plan={plan_result.plan_code} "
        f"inserted={plan_result.inserted} "
        f"updated={plan_result.updated} "
        f"pruned={plan_result.pruned}"
    )


__all__ = [
    "register",
    "handle_sync_entitlements",
]
