"""Dataclasses and helpers for usage report generation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


@dataclass(slots=True)
class UsageReportRequest:
    """Filters and knobs that drive report generation."""

    database_url: str
    period_start: datetime | None = None
    period_end: datetime | None = None
    tenant_slugs: tuple[str, ...] = ()
    plan_codes: tuple[str, ...] = ()
    feature_keys: tuple[str, ...] = ()
    include_inactive: bool = False
    warn_threshold: float = 0.8


@dataclass(slots=True)
class FeatureUsageSnapshot:
    feature_key: str
    display_name: str
    unit: str
    quantity: int
    soft_limit: int | None
    hard_limit: int | None
    remaining_to_soft_limit: int | None
    remaining_to_hard_limit: int | None
    percent_of_soft_limit: float | None
    percent_of_hard_limit: float | None
    status: str
    approaching: bool
    usage_window_start: datetime | None
    usage_window_end: datetime | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_key": self.feature_key,
            "display_name": self.display_name,
            "unit": self.unit,
            "quantity": self.quantity,
            "soft_limit": self.soft_limit,
            "hard_limit": self.hard_limit,
            "remaining_to_soft_limit": self.remaining_to_soft_limit,
            "remaining_to_hard_limit": self.remaining_to_hard_limit,
            "percent_of_soft_limit": self.percent_of_soft_limit,
            "percent_of_hard_limit": self.percent_of_hard_limit,
            "status": self.status,
            "approaching": self.approaching,
            "usage_window_start": isoformat(self.usage_window_start),
            "usage_window_end": isoformat(self.usage_window_end),
        }


@dataclass(slots=True)
class TenantUsageSnapshot:
    tenant_id: str
    tenant_slug: str
    tenant_name: str | None
    plan_code: str
    plan_name: str
    subscription_status: str
    window_start: datetime | None
    window_end: datetime | None
    features: list[FeatureUsageSnapshot] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "tenant_slug": self.tenant_slug,
            "tenant_name": self.tenant_name,
            "plan_code": self.plan_code,
            "plan_name": self.plan_name,
            "subscription_status": self.subscription_status,
            "window_start": isoformat(self.window_start),
            "window_end": isoformat(self.window_end),
            "features": [feature.to_dict() for feature in self.features],
        }


@dataclass(slots=True)
class UsageReport:
    generated_at: datetime
    applied_period_start: datetime | None
    applied_period_end: datetime | None
    tenant_filters: tuple[str, ...]
    plan_filters: tuple[str, ...]
    feature_filters: tuple[str, ...]
    warn_threshold: float
    include_inactive: bool
    tenants: list[TenantUsageSnapshot]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": isoformat(self.generated_at),
            "applied_period_start": isoformat(self.applied_period_start),
            "applied_period_end": isoformat(self.applied_period_end),
            "tenant_filters": list(self.tenant_filters),
            "plan_filters": list(self.plan_filters),
            "feature_filters": list(self.feature_filters),
            "warn_threshold": self.warn_threshold,
            "include_inactive": self.include_inactive,
            "tenant_count": len(self.tenants),
            "feature_count": sum(len(tenant.features) for tenant in self.tenants),
            "tenants": [tenant.to_dict() for tenant in self.tenants],
        }

    def iter_rows(self) -> Iterable[dict[str, Any]]:
        for tenant in self.tenants:
            for feature in tenant.features:
                yield {
                    "tenant_id": tenant.tenant_id,
                    "tenant_slug": tenant.tenant_slug,
                    "tenant_name": tenant.tenant_name,
                    "plan_code": tenant.plan_code,
                    "plan_name": tenant.plan_name,
                    "subscription_status": tenant.subscription_status,
                    "feature_key": feature.feature_key,
                    "feature_display_name": feature.display_name,
                    "unit": feature.unit,
                    "quantity": feature.quantity,
                    "soft_limit": feature.soft_limit,
                    "hard_limit": feature.hard_limit,
                    "remaining_to_soft_limit": feature.remaining_to_soft_limit,
                    "remaining_to_hard_limit": feature.remaining_to_hard_limit,
                    "percent_of_soft_limit": feature.percent_of_soft_limit,
                    "percent_of_hard_limit": feature.percent_of_hard_limit,
                    "status": feature.status,
                    "approaching": feature.approaching,
                    "window_start": isoformat(tenant.window_start),
                    "window_end": isoformat(tenant.window_end),
                    "usage_window_start": isoformat(feature.usage_window_start),
                    "usage_window_end": isoformat(feature.usage_window_end),
                }


@dataclass(slots=True)
class UsageReportArtifacts:
    json_path: Path | None
    csv_path: Path | None


def write_report_json(path: Path, report: UsageReport) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def write_report_csv(path: Path, report: UsageReport) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(report.iter_rows())
    fieldnames = list(rows[0].keys()) if rows else [
        "tenant_id",
        "tenant_slug",
        "tenant_name",
        "plan_code",
        "plan_name",
        "subscription_status",
        "feature_key",
        "feature_display_name",
        "unit",
        "quantity",
        "soft_limit",
        "hard_limit",
        "remaining_to_soft_limit",
        "remaining_to_hard_limit",
        "percent_of_soft_limit",
        "percent_of_hard_limit",
        "status",
        "approaching",
        "window_start",
        "window_end",
        "usage_window_start",
        "usage_window_end",
    ]

    import csv

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat()


__all__ = [
    "UsageReportRequest",
    "FeatureUsageSnapshot",
    "TenantUsageSnapshot",
    "UsageReport",
    "UsageReportArtifacts",
    "write_report_json",
    "write_report_csv",
    "isoformat",
]
