from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from starter_console.core import CLIContext, CLIError
from starter_console.ports.console import ConsolePort
from starter_console.workflows.usage import (
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


@dataclass(frozen=True, slots=True)
class UsageExportConfig:
    period_start: str | None
    period_end: str | None
    tenants: Sequence[str] | None
    plans: Sequence[str] | None
    features: Sequence[str] | None
    include_inactive: bool
    warn_threshold: float
    output_json: str | None
    output_csv: str | None
    no_json: bool
    no_csv: bool


@dataclass(frozen=True, slots=True)
class UsageSyncConfig:
    path: str | None
    plans: Sequence[str] | None
    prune_missing: bool
    dry_run: bool
    allow_disabled_artifact: bool


@dataclass(frozen=True, slots=True)
class UsageExportResult:
    report: UsageReport
    artifacts: UsageReportArtifacts


def export_usage_report(ctx: CLIContext, config: UsageExportConfig) -> UsageExportResult:
    console = ctx.console
    settings = ctx.require_settings()
    database_url = getattr(settings, "database_url", None)
    if not database_url:
        raise CLIError(
            "DATABASE_URL is not configured; run the wizard or pass --env-file to load it."
        )

    warn_threshold = config.warn_threshold
    if warn_threshold <= 0 or warn_threshold > 1:
        raise CLIError("--warn-threshold must be between 0 and 1.")

    period_start = _parse_datetime(config.period_start) if config.period_start else None
    period_end = _parse_datetime(config.period_end) if config.period_end else None

    request = UsageReportRequest(
        database_url=database_url,
        period_start=period_start,
        period_end=period_end,
        tenant_slugs=_to_tuple(config.tenants),
        plan_codes=_to_tuple(config.plans),
        feature_keys=_to_tuple(config.features),
        include_inactive=config.include_inactive,
        warn_threshold=warn_threshold,
    )

    json_path, csv_path = _resolve_output_targets(ctx, config)

    service = UsageReportService()
    try:
        report = asyncio.run(service.generate_report(request))
    except UsageReportError as exc:
        raise CLIError(str(exc)) from exc

    artifacts = write_usage_report_files(report, json_path=json_path, csv_path=csv_path)
    _render_report_summary(console, report, artifacts)
    console.success(
        f"Usage report generated for {len(report.tenants)} tenant(s).",
        topic="usage",
    )
    return UsageExportResult(report=report, artifacts=artifacts)


async def sync_usage_entitlements_with_config(
    ctx: CLIContext, config: UsageSyncConfig
) -> UsageEntitlementSyncResult:
    console = ctx.console
    settings = ctx.require_settings()
    database_url = getattr(settings, "database_url", None)
    if not database_url:
        raise CLIError(
            "DATABASE_URL is not configured; run the wizard or pass --env-file to load it."
        )

    artifact_path = _resolve_artifact_path(ctx, config.path)
    plan_filter = _to_tuple(config.plans) if config.plans else None

    try:
        result = await sync_usage_entitlements(
            database_url=database_url,
            artifact_path=artifact_path,
            plan_filter=plan_filter,
            prune_missing=config.prune_missing,
            dry_run=config.dry_run,
            allow_disabled_artifact=config.allow_disabled_artifact,
        )
    except EntitlementLoaderError as exc:
        raise CLIError(str(exc)) from exc

    _render_summary(console, result)
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
    return result


def _resolve_artifact_path(ctx: CLIContext, override: str | None) -> Path:
    if override:
        path = Path(override).expanduser().resolve()
    else:
        path = ctx.project_root / "var" / "reports" / "usage-entitlements.json"
    if not path.exists():
        raise CLIError(f"Entitlement artifact not found at {path}.")
    return path


def _resolve_output_targets(
    ctx: CLIContext, config: UsageExportConfig
) -> tuple[Path | None, Path | None]:
    default_json = ctx.project_root / "var" / "reports" / "usage-dashboard.json"
    default_csv = ctx.project_root / "var" / "reports" / "usage-dashboard.csv"

    json_path = None if config.no_json else _build_output_path(config.output_json, default_json)
    csv_path = None if config.no_csv else _build_output_path(config.output_csv, default_csv)

    if json_path is None and csv_path is None:
        raise CLIError("At least one artifact (JSON or CSV) must be enabled.")

    return json_path, csv_path


def _build_output_path(override: str | None, default_path: Path) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return default_path


def _to_tuple(items: Sequence[str] | None) -> tuple[str, ...]:
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


def _render_summary(console: ConsolePort, result: UsageEntitlementSyncResult) -> None:
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


def _render_report_summary(
    console: ConsolePort,
    report: UsageReport,
    artifacts: UsageReportArtifacts,
) -> None:
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
    "UsageExportConfig",
    "UsageExportResult",
    "UsageSyncConfig",
    "export_usage_report",
    "sync_usage_entitlements_with_config",
]
