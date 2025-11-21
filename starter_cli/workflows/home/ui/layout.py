from __future__ import annotations

from rich import box
from rich.console import Group, RenderableType
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from starter_cli.core.status_models import ActionShortcut, ProbeResult, ServiceStatus
from starter_cli.workflows.home.ui.widgets import probes_panel, services_table, shortcuts_panel


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
        Layout(name="body"),
        Layout(name="footer", size=7),
    )
    show_services = _should_show_services(services)
    if show_services:
        layout["body"].split_row(
            Layout(name="probes"),
            Layout(name="services", size=40),
        )
    else:
        layout["body"].split_row(Layout(name="probes"))
    layout["footer"].split_column(
        Layout(name="footer_shortcuts", size=6),
        Layout(name="footer_summary", size=1),
    )
    layout["probes"].update(Panel(probes_panel(probes), title="Probes", border_style="magenta"))
    if show_services:
        layout["services"].update(_services_panel(services))
    layout["footer_shortcuts"].update(_shortcuts_panel(shortcuts))
    layout["footer_summary"].update(_summary_line(summary, profile, strict))
    return layout


def _services_panel(services: list[ServiceStatus]) -> Panel:
    if not services:
        return Panel(Text("No services detected"), title="Services", border_style="cyan")
    return Panel(Group(services_table(services)), title="Services", border_style="cyan")


def _shortcuts_panel(shortcuts: list[ActionShortcut]) -> Panel:
    shortcuts_content: RenderableType
    if not shortcuts:
        shortcuts_content = Text("No shortcuts available")
    else:
        shortcuts_content = shortcuts_panel(shortcuts, bordered=False)
    return Panel(
        shortcuts_content,
        title="Shortcuts",
        border_style="green",
        box=box.SQUARE,
        padding=(0, 1),
    )


def _summary_line(summary: dict[str, int], profile: str, strict: bool) -> Text:
    text = Text()
    text.append("Profile: ", style="dim")
    text.append(profile, style="bold cyan")
    text.append("  Strict: ", style="dim")
    text.append("yes" if strict else "no", style="bold magenta" if strict else "bold green")
    text.append("  Probes ", style="dim")
    text.append(f"ok={summary.get('ok',0)} ", style="bold green")
    text.append(f"warn={summary.get('warn',0)} ", style="bold yellow")
    text.append(f"error={summary.get('error',0)} ", style="bold red")
    text.append(f"skipped={summary.get('skipped',0)}", style="bright_black")
    return text


def _should_show_services(services: list[ServiceStatus]) -> bool:
    if not services:
        return False
    # Hide when services mirror probes (backend/frontend) to avoid duplication; show when others appear.
    known_duplicates = {"backend", "frontend"}
    labels = {svc.label for svc in services}
    return any(label not in known_duplicates for label in labels)


__all__ = ["build_home_layout"]
