from __future__ import annotations

from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from starter_cli.core.status_models import ProbeResult, ServiceStatus
from starter_cli.workflows.home.ui.widgets import state_chip


def build_home_layout(
    *,
    probes: list[ProbeResult],
    services: list[ServiceStatus],
    summary: dict[str, int],
    profile: str,
    strict: bool,
) -> Layout:
    layout = Layout(name="root")
    layout.split_column(
        Layout(name="summary", size=6),
        Layout(name="body"),
    )
    layout["body"].split_row(
        Layout(name="probes"),
        Layout(name="services", size=40),
    )
    layout["summary"].update(_summary_panel(summary, profile, strict))
    layout["probes"].update(_probes_panel(probes))
    layout["services"].update(_services_panel(services))
    return layout


def _summary_panel(summary: dict[str, int], profile: str, strict: bool) -> Panel:
    text = Text()
    text.append(f"Profile: {profile}\n")
    text.append(f"Strict: {'yes' if strict else 'no'}\n")
    text.append(
        f"Probes → ok={summary.get('ok',0)}, warn={summary.get('warn',0)}, "
        f"error={summary.get('error',0)}, skipped={summary.get('skipped',0)}"
    )
    return Panel(text, title="Overview", border_style="cyan")


def _probes_panel(probes: list[ProbeResult]) -> Panel:
    table = Table(box=None, expand=True, show_edge=False, show_header=True, header_style="bold")
    table.add_column("Status", no_wrap=True)
    table.add_column("Probe")
    table.add_column("Detail")
    for probe in sorted(probes, key=lambda p: (-p.severity_rank, p.name)):
        table.add_row(state_chip(probe.state), probe.name, probe.detail or "")
    return Panel(table, title="Probes", border_style="magenta")


def _services_panel(services: list[ServiceStatus]) -> Panel:
    if not services:
        return Panel(Text("No services detected"), title="Services", border_style="cyan")
    table = Table(box=None, expand=True, show_edge=False, show_header=True, header_style="bold")
    table.add_column("Status", no_wrap=True)
    table.add_column("Service")
    table.add_column("Endpoint")
    table.add_column("Detail")
    for svc in sorted(services, key=lambda s: (-s.severity_rank, s.label)):
        endpoint = ", ".join(svc.endpoints) if svc.endpoints else ""
        table.add_row(state_chip(svc.state), svc.label, endpoint, svc.detail or "")
    return Panel(Group(table), title="Services", border_style="cyan")


__all__ = ["build_home_layout"]
