from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

DEFAULT_LOG_ROOT = Path("var/log")
_WARNING_STATES = {
    "approaching",
    "soft_limit_exceeded",
    "hard_limit_exceeded",
}


@dataclass(frozen=True, slots=True)
class LogEntry:
    name: str
    path: Path
    exists: bool


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


def resolve_log_root(project_root: Path, env: Mapping[str, str]) -> Path:
    raw = env.get("LOG_ROOT") or str(DEFAULT_LOG_ROOT)
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()
    return candidate


def resolve_log_root_override(
    project_root: Path,
    env: Mapping[str, str],
    *,
    override: Path | None,
) -> Path:
    if override is not None:
        candidate = override.expanduser()
        if not candidate.is_absolute():
            candidate = (project_root / candidate).resolve()
        return candidate
    return resolve_log_root(project_root, env)


def resolve_active_log_dir(log_root: Path) -> Path:
    current = log_root / "current"
    if current.exists():
        return current.resolve()
    if not log_root.exists():
        return log_root
    dated_dirs = [
        entry
        for entry in log_root.iterdir()
        if entry.is_dir() and _is_date_dir(entry.name)
    ]
    if not dated_dirs:
        return log_root
    latest = max(dated_dirs, key=lambda entry: entry.name)
    return latest.resolve()


def collect_log_entries(log_dir: Path) -> list[LogEntry]:
    entries: list[LogEntry] = []
    candidates = {
        "api/all.log": log_dir / "api" / "all.log",
        "api/error.log": log_dir / "api" / "error.log",
        "frontend/all.log": log_dir / "frontend" / "all.log",
        "frontend/error.log": log_dir / "frontend" / "error.log",
    }
    for name, path in candidates.items():
        entries.append(LogEntry(name=name, path=path, exists=path.exists()))

    cli_dir = log_dir / "cli"
    cli_files = list(cli_dir.glob("*.log")) if cli_dir.exists() else []
    entries.append(
        LogEntry(
            name="cli/*.log",
            path=cli_dir,
            exists=bool(cli_files),
        )
    )
    return entries


def mask_value(value: str | None) -> str:
    if not value:
        return "(missing)"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


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


def _is_date_dir(name: str) -> bool:
    try:
        date.fromisoformat(name)
    except ValueError:
        return False
    return True


__all__ = [
    "DEFAULT_LOG_ROOT",
    "LogEntry",
    "UsageReport",
    "UsageSummary",
    "UsageWarning",
    "collect_log_entries",
    "load_usage_report",
    "load_usage_summary",
    "mask_value",
    "resolve_active_log_dir",
    "resolve_log_root",
    "resolve_log_root_override",
]
