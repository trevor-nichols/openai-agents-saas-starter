from __future__ import annotations

import argparse
import asyncio

from starter_console.core import CLIContext
from starter_console.services.usage.usage_ops import (
    UsageExportConfig,
    UsageSyncConfig,
    export_usage_report,
    sync_usage_entitlements_with_config,
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
    config = UsageSyncConfig(
        path=args.path,
        plans=args.plan or None,
        prune_missing=args.prune_missing,
        dry_run=args.dry_run,
        allow_disabled_artifact=args.allow_disabled_artifact,
    )
    asyncio.run(sync_usage_entitlements_with_config(ctx, config))
    return 0


def handle_export_report(args: argparse.Namespace, ctx: CLIContext) -> int:
    config = UsageExportConfig(
        period_start=args.period_start,
        period_end=args.period_end,
        tenants=args.tenant or None,
        plans=args.plan or None,
        features=args.feature or None,
        include_inactive=args.include_inactive,
        warn_threshold=args.warn_threshold,
        output_json=args.output_json,
        output_csv=args.output_csv,
        no_json=args.no_json,
        no_csv=args.no_csv,
    )
    export_usage_report(ctx, config)
    return 0


__all__ = ["register", "handle_sync_entitlements", "handle_export_report"]
