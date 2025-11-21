from __future__ import annotations

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from typing import Mapping, Sequence

from starter_cli.core.status_models import ActionShortcut, ProbeResult, ProbeState, ServiceStatus


def state_chip(state: ProbeState) -> Text:
    colors = {
        ProbeState.OK: "bold green",
        ProbeState.WARN: "bold yellow",
        ProbeState.ERROR: "bold red",
        ProbeState.SKIPPED: "bright_black",
    }
    return Text(state.value.upper(), style=colors.get(state, "white"))


def shortcuts_panel(shortcuts: list[ActionShortcut], *, bordered: bool = True) -> Table:
    table = Table(
        box=None if not bordered else box.SQUARE,
        expand=True,
        show_edge=False,
        show_header=False,
        padding=(0, 1),
    )
    for shortcut in shortcuts:
        key = Text(shortcut.key, style="bold cyan")
        label = Text(shortcut.label, style="bold white")
        desc = Text(shortcut.description or "", style="dim")
        table.add_row(key, label, desc)
    return table


def probes_table(probes: list[ProbeResult]) -> Table:
    table = Table(box=None, expand=True, show_edge=False, show_header=True, header_style="bold")
    table.add_column("Status", no_wrap=True)
    table.add_column("Probe")
    table.add_column("Detail")
    for probe in sorted(probes, key=lambda p: (-p.severity_rank, p.name)):
        table.add_row(state_chip(probe.state), Text(probe.name, style="bold white"), probe.detail or "")
    return table


def probes_panel(probes: list[ProbeResult]) -> Group:
    sections = []
    for category, rows in _group_probes_by_category(probes):
        table = Table(box=None, expand=True, show_edge=False, show_header=True, header_style="bold")
        table.add_column("Status", no_wrap=True)
        table.add_column("Probe")
        table.add_column("Detail")
        for probe in rows:
            table.add_row(
                state_chip(probe.state),
                Text(probe.name, style="bold white"),
                _render_probe_detail(probe),
            )
        sections.append(
            Panel(
                table,
                title=category.upper(),
                border_style=_CATEGORY_STYLE.get(category, "bright_black"),
                box=box.SQUARE,
                padding=(0, 1),
            )
        )
    return Group(*sections) if sections else Group()


def services_table(services: list[ServiceStatus]) -> Table:
    table = Table(box=None, expand=True, show_edge=False, show_header=True, header_style="bold")
    table.add_column("Status", no_wrap=True)
    table.add_column("Service")
    table.add_column("Endpoint")
    table.add_column("Detail")
    for svc in sorted(services, key=lambda s: (-s.severity_rank, s.label)):
        endpoint = ", ".join(svc.endpoints) if svc.endpoints else ""
        table.add_row(state_chip(svc.state), svc.label, endpoint, svc.detail or "")
    return table


_CATEGORY_ORDER = {"core": 0, "secrets": 1, "billing": 2}
_CATEGORY_STYLE = {"core": "bright_black", "secrets": "magenta", "billing": "yellow"}


def _group_probes_by_category(
    probes: list[ProbeResult],
) -> list[tuple[str, list[ProbeResult]]]:
    buckets: dict[str, list[ProbeResult]] = {}
    for probe in probes:
        category = str(probe.metadata.get("category")) if hasattr(probe, "metadata") else "other"
        buckets.setdefault(category, []).append(probe)

    def cat_key(item: tuple[str, list[ProbeResult]]) -> tuple[int, str]:
        category, _ = item
        return (_CATEGORY_ORDER.get(category, 99), category)

    ordered: list[tuple[str, list[ProbeResult]]] = []
    for category, rows in sorted(buckets.items(), key=cat_key):
        rows_sorted = sorted(rows, key=lambda p: (-p.severity_rank, p.name))
        ordered.append((category, rows_sorted))
    return ordered


# ---------------------------------------------------------------------------
# Detail renderers
# ---------------------------------------------------------------------------


def _render_probe_detail(probe: ProbeResult) -> Text:
    name = probe.name
    if name == "environment":
        return _env_detail(probe)
    if name == "ports":
        return _ports_detail(probe)
    if name == "database":
        return _db_detail(probe)
    if name == "redis":
        return _redis_detail(probe)
    if name in {"api", "frontend"}:
        return _http_detail(probe)
    if name == "migrations":
        return _migrations_detail(probe)
    if name == "secrets":
        return _secrets_detail(probe)
    if name == "billing":
        return _billing_detail(probe)
    # fallback
    return Text(probe.detail or "", style="bright_black" if not probe.detail else "")


def _env_detail(probe: ProbeResult) -> Text:
    md = probe.metadata or {}
    coverage_raw = md.get("coverage")
    coverage = coverage_raw if isinstance(coverage_raw, (int, float)) else None
    missing_raw = md.get("missing", [])
    missing: list[str] = list(missing_raw) if isinstance(missing_raw, Sequence) else []
    text = Text()
    if coverage is not None:
        pct = round(coverage * 100)
        text.append(f"{pct}%", style=_coverage_style(pct))
    if missing:
        text.append("  missing: ", style="dim")
        text.append(_list_preview(missing), style="bright_black")
    else:
        text.append("  all set", style="bright_black")
    if not text.plain.strip() and probe.detail:
        return Text(probe.detail)
    return text


def _ports_detail(probe: ProbeResult) -> Text:
    text = Text()
    detail = probe.detail or ""
    parts = [p.strip() for p in detail.split(",") if p.strip()]
    if not parts:
        return Text(detail)
    for idx, part in enumerate(parts):
        # expected format: label:host:port=up/down
        label, status = (part.split("=", 1) + [""])[:2] if "=" in part else (part, "")
        status_style = "bold green" if status == "up" else "bold red"
        text.append(label, style="cyan")
        text.append(" ")
        text.append(status or "", style=status_style)
        if idx < len(parts) - 1:
            text.append("   ", style="dim")
    return text if text.plain else Text(detail)


def _db_detail(probe: ProbeResult) -> Text:
    md = probe.metadata or {}
    host = md.get("host")
    port = md.get("port")
    ping_raw = md.get("ping")
    ping = ping_raw if isinstance(ping_raw, str) else None
    text = Text()
    if host and port:
        text.append(f"{host}:{port}", style="cyan")
    if ping:
        text.append("  ping:", style="dim")
        text.append(f"{ping}", style=_ping_style(ping))
    if not text.plain and probe.detail:
        return Text(probe.detail)
    if not text.plain:
        text.append("unavailable", style="bright_black")
    return text


def _redis_detail(probe: ProbeResult) -> Text:
    md = probe.metadata or {}
    host = md.get("host")
    port = md.get("port")
    ping_raw = md.get("ping")
    ping = ping_raw if isinstance(ping_raw, str) else None
    text = Text()
    if host and port:
        text.append(f"{host}:{port}", style="cyan")
    if ping:
        text.append("  ping:", style="dim")
        text.append(f"{ping}", style=_ping_style(ping))
    if not text.plain and probe.detail:
        return Text(probe.detail)
    if not text.plain:
        text.append("unavailable", style="bright_black")
    return text


def _http_detail(probe: ProbeResult) -> Text:
    md = probe.metadata or {}
    status_raw = md.get("status")
    status = int(status_raw) if isinstance(status_raw, (int, str)) and str(status_raw).isdigit() else None
    url_raw = md.get("url")
    url = str(url_raw) if isinstance(url_raw, str) else None
    text = Text()
    if status is not None:
        text.append(str(status), style=_status_style(int(status)))
    elif probe.detail:
        text.append(probe.detail, style="bright_black")
    if url:
        text.append("  ")
        text.append(_truncate_url(url), style="dim")
    return text if text.plain else Text(probe.detail or "")


def _migrations_detail(probe: ProbeResult) -> Text:
    md = probe.metadata or {}
    local = md.get("local_head")
    db = md.get("db_revision")
    text = Text()
    if local:
        text.append("code:", style="dim")
        text.append(str(local), style="cyan")
    if db:
        text.append("  db:", style="dim")
        text.append(str(db), style="bold green" if db == local else "bold yellow")
    if not text.plain and probe.detail:
        return Text(probe.detail)
    if not text.plain:
        text.append("unknown", style="bright_black")
    return text


def _secrets_detail(probe: ProbeResult) -> Text:
    md = probe.metadata or {}
    provider = str(md.get("provider", "unset"))
    missing_raw = md.get("missing", [])
    missing: list[str] = list(missing_raw) if isinstance(missing_raw, Sequence) else []
    base_url_raw = md.get("base_url")
    base_url = str(base_url_raw) if isinstance(base_url_raw, str) else None
    region_raw = md.get("region")
    region = str(region_raw) if isinstance(region_raw, str) else None
    auth_raw = md.get("auth")
    auth = str(auth_raw) if isinstance(auth_raw, str) else None
    text = Text()
    text.append(str(provider), style="magenta")
    if missing:
        text.append("  missing: ", style="dim")
        text.append(_list_preview(missing), style="bright_black")
    if base_url:
        text.append("  ")
        text.append(_truncate_url(base_url), style="dim")
    if region:
        text.append("  ")
        text.append(region, style="cyan")
    if auth:
        text.append("  ")
        text.append(auth, style="bright_black")
    if not text.plain and probe.detail:
        return Text(probe.detail)
    return text


def _billing_detail(probe: ProbeResult) -> Text:
    md = probe.metadata or {}
    provider = str(md.get("provider", "stripe"))
    status_raw = md.get("status")
    status = int(status_raw) if isinstance(status_raw, (int, str)) and str(status_raw).isdigit() else None
    reason_raw = md.get("reason")
    reason = str(reason_raw) if isinstance(reason_raw, str) else None
    text = Text()
    text.append(str(provider), style="yellow")
    if status is not None:
        text.append("  ")
        text.append(str(status), style=_status_style(int(status)))
    if reason:
        text.append("  ")
        text.append(reason, style="bright_black")
    if probe.detail and not text.plain:
        return Text(probe.detail)
    if probe.detail and text.plain:
        text.append("  ")
        text.append(probe.detail, style="bright_black")
    return text if text.plain else Text("billing")


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _coverage_style(pct: int) -> str:
    if pct >= 90:
        return "bold green"
    if pct >= 70:
        return "bold yellow"
    return "bold red"


def _ping_style(ping: str) -> str:
    if ping == "ok":
        return "bold green"
    if ping == "skipped":
        return "bright_black"
    return "bold red"


def _status_style(code: int) -> str:
    if 200 <= code < 300:
        return "bold green"
    if 300 <= code < 400:
        return "cyan"
    if 400 <= code < 500:
        return "bold yellow"
    return "bold red"


def _truncate_url(url: str, *, max_len: int = 48) -> str:
    if len(url) <= max_len:
        return url
    return url[: max_len - 3] + "..."


def _list_preview(items: list[str], *, max_items: int = 3) -> str:
    if len(items) <= max_items:
        return ", ".join(items)
    head = ", ".join(items[:max_items])
    return f"{head} +{len(items) - max_items} more"


__all__ = ["state_chip", "shortcuts_panel", "probes_table", "probes_panel", "services_table"]
