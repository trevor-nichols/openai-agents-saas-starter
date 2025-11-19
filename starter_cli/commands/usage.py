from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
from pathlib import Path

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext, CLIError
from starter_cli.workflows.usage import (
    EntitlementLoaderError,
    PlanSyncResult,
    UsageEntitlementSyncResult,
    UsageReport,
    UsageReportArtifacts,
    UsageReportError,
    UsageReportRequest,
    UsageReportService,
    sync_usage_entitlements,
    write_usage_report_files,
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

    export_parser = usage_subparsers.add_parser(
        "export-report",
        help="Generate per-tenant usage dashboard artifacts (JSON/CSV).",
    )
    export_parser.add_argument(
        "--period-start",
        metavar="TIMESTAMP",
        help="Override the window start (ISO 8601). Defaults to subscription period.",
    )
    export_parser.add_argument(
        "--period-end",
        metavar="TIMESTAMP",
        help="Override the window end (ISO 8601). Defaults to subscription period.",
    )
    export_parser.add_argument(
        "--tenant",
        action="append",
        metavar="SLUG",
        help="Limit the report to one or more tenant slugs (repeatable).",
    )
    export_parser.add_argument(
        "--plan",
        action="append",
        metavar="CODE",
        help="Limit to one or more plan codes (repeatable).",
    )
    export_parser.add_argument(
        "--feature",
        action="append",
        metavar="KEY",
        help="Limit to one or more feature keys (repeatable).",
    )
    export_parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include inactive/cancelled subscriptions (default: only active).",
    )
    export_parser.add_argument(
        "--warn-threshold",
        type=float,
        default=0.8,
        help="Fraction (0-1) of limit that counts as 'approaching' (default: 0.8).",
    )
    export_parser.add_argument(
        "--output-json",
        metavar="PATH",
        help=(
            "Write JSON artifact (default: var/reports/usage-dashboard.json). "
            "Pass --no-json to skip."
        ),
    )
    export_parser.add_argument(
        "--output-csv",
        metavar="PATH",
        help=(
            "Write CSV artifact (default: var/reports/usage-dashboard.csv). "
            "Pass --no-csv to skip."
        ),
    )
    export_parser.add_argument(
        "--no-json",
        action="store_true",
        help="Skip writing the JSON artifact.",
    )
    export_parser.add_argument(
        "--no-csv",
        action="store_true",
        help="Skip writing the CSV artifact.",
    )
    export_parser.set_defaults(handler=handle_export_report)


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


def handle_export_report(args: argparse.Namespace, ctx: CLIContext) -> int:
    settings = ctx.require_settings()
    database_url = getattr(settings, "database_url", None)
    if not database_url:
        raise CLIError(
            "DATABASE_URL is not configured; run the wizard or pass --env-file to load it."
        )

    warn_threshold = args.warn_threshold
    if warn_threshold <= 0 or warn_threshold > 1:
        raise CLIError("--warn-threshold must be between 0 and 1.")

    period_start = _parse_datetime(args.period_start) if args.period_start else None
    period_end = _parse_datetime(args.period_end) if args.period_end else None

    request = UsageReportRequest(
        database_url=database_url,
        period_start=period_start,
        period_end=period_end,
        tenant_slugs=_to_tuple(args.tenant),
        plan_codes=_to_tuple(args.plan),
        feature_keys=_to_tuple(args.feature),
        include_inactive=args.include_inactive,
        warn_threshold=warn_threshold,
    )

    json_path, csv_path = _resolve_output_targets(ctx, args)

    service = UsageReportService()
    try:
        report = asyncio.run(service.generate_report(request))
    except UsageReportError as exc:
        raise CLIError(str(exc)) from exc

    artifacts = write_usage_report_files(report, json_path=json_path, csv_path=csv_path)

    _render_report_summary(report, artifacts)
    console.success(
        f"Usage report generated for {len(report.tenants)} tenant(s).",
        topic="usage",
    )
    return 0


def _to_tuple(items: list[str] | None) -> tuple[str, ...]:
    if not items:
        return ()
    cleaned = [item.strip() for item in items if item and item.strip()]
    return tuple(dict.fromkeys(cleaned))


def _parse_datetime(raw: str) -> datetime:
    text_value = raw.strip()
    if not text_value:
        raise CLIError("Timestamp cannot be empty.")
    text_value = text_value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text_value)
    except ValueError as exc:
        raise CLIError(f"Invalid timestamp '{raw}': {exc}") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _resolve_output_targets(
    ctx: CLIContext, args: argparse.Namespace
) -> tuple[Path | None, Path | None]:
    default_json = ctx.project_root / "var" / "reports" / "usage-dashboard.json"
    default_csv = ctx.project_root / "var" / "reports" / "usage-dashboard.csv"

    json_path = None if args.no_json else _build_output_path(args.output_json, default_json)
    csv_path = None if args.no_csv else _build_output_path(args.output_csv, default_csv)

    if json_path is None and csv_path is None:
        raise CLIError("At least one artifact (JSON or CSV) must be enabled.")

    return json_path, csv_path


def _build_output_path(override: str | None, default_path: Path) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return default_path


def _render_report_summary(report: UsageReport, artifacts: UsageReportArtifacts) -> None:
    console.info(
        (
            f"Tenants processed: {len(report.tenants)} | "
            f"Features evaluated: {sum(len(t.features) for t in report.tenants)}"
        ),
        topic="usage",
    )
    if artifacts.json_path:
        console.info(f"JSON artifact: {artifacts.json_path}", topic="usage")
    if artifacts.csv_path:
        console.info(f"CSV artifact: {artifacts.csv_path}", topic="usage")

    approaching = []
    for tenant in report.tenants:
        for feature in tenant.features:
            if feature.status in {"approaching", "soft_limit_exceeded", "hard_limit_exceeded"}:
                approaching.append((tenant.tenant_slug, feature.feature_key, feature.status))

    if approaching:
        preview = ", ".join(
            f"{slug}:{feature} ({status})" for slug, feature, status in approaching[:5]
        )
        console.warn(
            f"Approaching/over limit features: {preview}",
            topic="usage",
        )


__all__ = [
    "register",
    "handle_sync_entitlements",
]
