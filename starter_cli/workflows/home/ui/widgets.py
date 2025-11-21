from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from starter_cli.core.status_models import ActionShortcut, ProbeResult, ProbeState, ServiceStatus


def state_chip(state: ProbeState) -> Text:
    colors = {
        ProbeState.OK: "bold green",
        ProbeState.WARN: "bold yellow",
        ProbeState.ERROR: "bold red",
        ProbeState.SKIPPED: "bright_black",
    }
    return Text(state.value.upper(), style=colors.get(state, "white"))


def shortcuts_panel(shortcuts: list[ActionShortcut]) -> Panel:
    table = Table(box=None, expand=True, show_edge=False, show_header=False, padding=(0, 1))
    for shortcut in shortcuts:
        key = Text(shortcut.key, style="bold cyan")
        label = Text(shortcut.label, style="bold white")
        desc = Text(shortcut.description or "", style="dim")
        table.add_row(key, label, desc)
    return Panel(table, title="Shortcuts", border_style="green")


def probes_table(probes: list[ProbeResult]) -> Table:
    table = Table(box=None, expand=True, show_edge=False, show_header=True, header_style="bold")
    table.add_column("Status", no_wrap=True)
    table.add_column("Probe")
    table.add_column("Detail")
    for probe in sorted(probes, key=lambda p: (-p.severity_rank, p.name)):
        table.add_row(state_chip(probe.state), probe.name, probe.detail or "")
    return table


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


__all__ = ["state_chip", "shortcuts_panel", "probes_table", "services_table"]
