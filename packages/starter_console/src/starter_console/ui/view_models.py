from __future__ import annotations

from datetime import datetime

from starter_console.core.status_models import ProbeResult, ProbeState, ServiceStatus
from starter_console.workflows.setup_menu.models import SetupItem


def status_label(state: ProbeState) -> str:
    return state.value.upper()


def format_summary(
    summary: dict[str, int],
    *,
    profile: str,
    strict: bool,
    stack_state: str | None,
) -> str:
    strict_label = "yes" if strict else "no"
    stack_label = stack_state or "unknown"
    ok = summary.get("ok", 0)
    warn = summary.get("warn", 0)
    error = summary.get("error", 0)
    skipped = summary.get("skipped", 0)
    lines = [
        f"Environment: {profile} | Strict: {strict_label}",
        f"Stack: {stack_label}",
        f"Probe summary: ok={ok} warn={warn} error={error} skipped={skipped}",
    ]
    return "\n".join(lines)


def sort_probes(probes: list[ProbeResult]) -> list[ProbeResult]:
    return sorted(probes, key=lambda probe: (-probe.severity_rank, probe.name))


def probe_rows(probes: list[ProbeResult]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for probe in sort_probes(probes):
        rows.append(
            (
                probe.name,
                status_label(probe.state),
                probe.detail or "—",
            )
        )
    return rows


def service_rows(services: list[ServiceStatus]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for service in services:
        detail = service.detail or "—"
        if service.endpoints:
            detail = f"{detail} ({', '.join(service.endpoints)})"
        rows.append(
            (
                service.label,
                status_label(service.state),
                detail,
            )
        )
    return rows


def setup_row(item: SetupItem) -> tuple[str, str, str, str, str]:
    status = item.status.upper()
    detail = item.detail or ""
    if item.optional and item.status in {"missing", "unknown"}:
        detail = (detail + " " if detail else "") + "(optional)"
    if item.progress_label:
        progress = item.progress_label
    elif item.progress is None:
        progress = "—"
    else:
        progress = f"{max(0, min(int(item.progress * 100), 100))}%"
    last_run = item.last_run.isoformat(timespec="seconds") if item.last_run else "—"
    return (status, item.label, detail, progress, last_run)


def format_timestamp(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.isoformat(timespec="seconds")


__all__ = [
    "format_summary",
    "format_timestamp",
    "probe_rows",
    "service_rows",
    "setup_row",
    "sort_probes",
    "status_label",
]
