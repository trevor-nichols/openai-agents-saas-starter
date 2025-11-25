from __future__ import annotations

from rich.console import Group, RenderableType
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .state import WizardUIViewState
from .widgets import progress_bar, progress_caption, status_badge
from .widgets.sections import section_card


def build_layout(state: WizardUIViewState) -> Layout:
    layout = Layout(name="root")
    layout.split_column(
        Layout(name="upper", ratio=3),
        Layout(name="activity", size=9),
    )
    layout["upper"].split_row(
        Layout(name="sections"),
        Layout(name="automation", size=48),
    )
    layout["sections"].update(_build_sections_panel(state))
    layout["automation"].update(_build_automation_panel(state))
    layout["activity"].update(_build_activity_panel(state))
    return layout


def _build_sections_panel(state: WizardUIViewState) -> Panel:
    current_label = None
    if state.current_section_key:
        for section in state.sections:
            if section.key == state.current_section_key:
                current_label = section.label
                break

    caption = progress_caption(
        completed=state.completed_sections,
        total=state.total_sections,
        current_label=current_label,
        elapsed=state.elapsed_text(),
    )
    bar = progress_bar(state.completed_sections, state.total_sections)

    cards = []
    for section in state.sections:
        expanded = (
            section.key == state.current_section_key or section.key in state.expanded_sections
        )
        cards.append(section_card(section, expanded=expanded))
    body = Group(caption, bar, *cards)
    return Panel(body, title="Milestones", border_style="cyan")


def _build_automation_panel(state: WizardUIViewState) -> Panel:
    table = Table(box=None, show_header=True, header_style="bold", expand=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Phase")
    table.add_column("Detail")
    for row in state.automation:
        table.add_row(
            status_badge(row.state),
            row.label,
            row.detail or "",
        )
    return Panel(table, title="Automation", border_style="magenta")


def _build_activity_panel(state: WizardUIViewState) -> Panel:
    body: RenderableType
    if not state.events:
        body = Text("No activity yet.")
    else:
        table = Table.grid(expand=True)
        table.add_column(style="log.time", width=8)
        table.add_column()
        for timestamp, event in state.events:
            table.add_row(timestamp, event)
        body = table
    return Panel(body, title="Activity", border_style="cyan")


__all__ = ["build_layout"]
