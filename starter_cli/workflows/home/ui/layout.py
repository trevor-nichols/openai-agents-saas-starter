from __future__ import annotations

from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from starter_cli.core.status_models import ActionShortcut, ProbeResult, ServiceStatus
from starter_cli.workflows.home.ui.widgets import (
    probes_table,
    services_table,
    shortcuts_panel,
    state_chip,
)


def build_home_layout(
    *,
    probes: list[ProbeResult],
    services: list[ServiceStatus],
    summary: dict[str, int],
    profile: str,
    strict: bool,
    shortcuts: list[ActionShortcut],
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
    layout["summary"].update(_summary_panel(summary, profile, strict, shortcuts))
    layout["probes"].update(Panel(probes_table(probes), title="Probes", border_style="magenta"))
    layout["services"].update(_services_panel(services))
    return layout


def _summary_panel(
    summary: dict[str, int], profile: str, strict: bool, shortcuts: list[ActionShortcut]
) -> Panel:
    text = Text()
    text.append(f"Profile: {profile}\n")
    text.append(f"Strict: {'yes' if strict else 'no'}\n")
    text.append(
        f"Probes → ok={summary.get('ok',0)}, warn={summary.get('warn',0)}, "
        f"error={summary.get('error',0)}, skipped={summary.get('skipped',0)}"
    )
    return Panel(
        Group(text, shortcuts_panel(shortcuts)),
        title="Overview",
        border_style="cyan",
    )


def _services_panel(services: list[ServiceStatus]) -> Panel:
    if not services:
        return Panel(Text("No services detected"), title="Services", border_style="cyan")
    return Panel(Group(services_table(services)), title="Services", border_style="cyan")


__all__ = ["build_home_layout"]
