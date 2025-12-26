from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_WARNING_STATES = {
    "approaching",
    "soft_limit_exceeded",
    "hard_limit_exceeded",
}


@dataclass(frozen=True, slots=True)
class UsageSummary:
    generated_at: str | None
    tenant_count: int
    feature_count: int
    warning_count: int


@dataclass(frozen=True, slots=True)
class UsageWarning:
    tenant_slug: str
    feature_key: str
    status: str


@dataclass(frozen=True, slots=True)
class UsageReport:
    summary: UsageSummary
    warnings: tuple[UsageWarning, ...]


def load_usage_report(path: Path, *, warning_limit: int = 5) -> UsageReport | None:
    if not path.exists():
        return None
    try:
        payload = _read_json(path)
    except Exception:
        return None
    tenants = _collect_tenants(payload)
    summary = _build_summary(payload, tenants)
    warnings = tuple(_collect_warning_rows(tenants, limit=warning_limit))
    return UsageReport(summary=summary, warnings=warnings)


def load_usage_summary(path: Path) -> UsageSummary | None:
    report = load_usage_report(path, warning_limit=0)
    if report is None:
        return None
    return report.summary


def _collect_tenants(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_tenants = payload.get("tenants")
    return (
        [tenant for tenant in raw_tenants if isinstance(tenant, dict)]
        if isinstance(raw_tenants, list)
        else []
    )


def _build_summary(payload: Mapping[str, Any], tenants: list[dict[str, Any]]) -> UsageSummary:
    generated_at = _as_str(payload.get("generated_at"))
    tenant_count = _as_int(payload.get("tenant_count"))
    if tenant_count == 0 and tenants:
        tenant_count = len(tenants)
    feature_count = _as_int(payload.get("feature_count"))
    if feature_count == 0 and tenants:
        feature_count = sum(len(tenant.get("features", [])) for tenant in tenants)
    warning_count = _count_warnings(tenants)
    return UsageSummary(
        generated_at=generated_at,
        tenant_count=tenant_count,
        feature_count=feature_count,
        warning_count=warning_count,
    )


def _collect_warning_rows(
    tenants: list[dict[str, Any]],
    *,
    limit: int,
) -> list[UsageWarning]:
    if limit <= 0:
        return []
    rows: list[UsageWarning] = []
    for tenant in tenants:
        slug = _as_str(tenant.get("tenant_slug")) or "unknown"
        features = tenant.get("features")
        if not isinstance(features, list):
            continue
        for feature in features:
            if not isinstance(feature, dict):
                continue
            status = feature.get("status")
            if status not in _WARNING_STATES:
                continue
            feature_key = _as_str(feature.get("feature_key")) or ""
            rows.append(UsageWarning(slug, feature_key, str(status)))
            if len(rows) >= limit:
                return rows
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _count_warnings(tenants: list[dict[str, Any]]) -> int:
    count = 0
    for tenant in tenants:
        features = tenant.get("features")
        if not isinstance(features, list):
            continue
        for feature in features:
            status = feature.get("status")
            if status in _WARNING_STATES:
                count += 1
    return count


__all__ = [
    "UsageReport",
    "UsageSummary",
    "UsageWarning",
    "load_usage_report",
    "load_usage_summary",
]
