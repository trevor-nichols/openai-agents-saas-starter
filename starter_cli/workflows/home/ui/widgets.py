from __future__ import annotations

from rich import box
from rich.console import Group
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
            table.add_row(state_chip(probe.state), Text(probe.name, style="bold white"), probe.detail or "")
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


__all__ = ["state_chip", "shortcuts_panel", "probes_table", "probes_panel", "services_table"]
