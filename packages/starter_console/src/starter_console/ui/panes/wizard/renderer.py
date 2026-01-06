from __future__ import annotations

from collections.abc import Iterable

from textual.widgets import DataTable, Static

from starter_console.workflows.setup.ui import WizardUIView
from starter_console.workflows.setup.ui.state import AutomationRow, SectionStatus, WizardUIViewState


def configure_tables(pane, state: WizardUIViewState) -> None:
    render_stepper(pane, state)
    render_sections(pane, [])
    render_automation(pane, [])
    render_conditional(pane, state)


def render_stepper(pane, state: WizardUIViewState) -> None:
    if not state.sections:
        pane.query_one("#wizard-stepper", Static).update(
            "Steps will appear once the wizard starts."
        )
        return
    lines: list[str] = ["Steps"]
    current_key = state.current_section_key
    for section in sorted(state.sections, key=lambda item: item.order):
        is_current = section.key == current_key or section.state == "running"
        token = _step_token(section.state, is_current=is_current)
        prefix = ">" if is_current else " "
        line = f"{prefix} {section.order:02d}. {token} {section.label}"
        if section.state not in {"pending", "running", "done"}:
            line += f" ({section.state})"
        lines.append(line)
    pane.query_one("#wizard-stepper", Static).update("\n".join(lines))


def _step_token(state: str, *, is_current: bool) -> str:
    if is_current:
        return "[>]"
    return {
        "done": "[x]",
        "failed": "[!]",
        "blocked": "[!]",
        "skipped": "[-]",
        "running": "[>]",
    }.get(state, "[ ]")


def render_sections(pane, sections: Iterable[SectionStatus]) -> None:
    table = pane.query_one("#wizard-sections", DataTable)
    table.clear(columns=True)
    table.add_columns("#", "Section", "Status", "Detail")
    for section in sections:
        table.add_row(
            str(section.order),
            section.label,
            section.state,
            section.detail or "",
        )


def render_automation(pane, automation: Iterable[AutomationRow]) -> None:
    table = pane.query_one("#wizard-automation", DataTable)
    table.clear(columns=True)
    table.add_columns("Status", "Phase", "Detail")
    for row in automation:
        table.add_row(row.state, row.label, row.detail or "")


def render_conditional(pane, state: WizardUIViewState) -> None:
    table = pane.query_one("#wizard-conditional", DataTable)
    table.clear(columns=True)
    table.add_columns("Prompt", "Configured", "Dependencies")
    current = None
    if state.current_section_key:
        current = next(
            (section for section in state.sections if section.key == state.current_section_key),
            None,
        )
    if not current:
        table.add_row("-", "-", "No active section")
        return
    prompts = [prompt for prompt in current.prompts if prompt.dependencies]
    if not prompts:
        table.add_row("-", "-", "No conditional prompts")
        return
    for prompt in prompts:
        deps = ", ".join(
            f"{dep.label}={'ok' if dep.satisfied else 'no'}" for dep in prompt.dependencies
        )
        table.add_row(prompt.label, "yes" if prompt.configured else "no", deps)


def render_activity(pane, events: Iterable[tuple[str, str]]) -> None:
    lines = [f"{timestamp} {message}" for timestamp, message in events]
    pane.query_one("#wizard-activity", Static).update("\n".join(lines))


def empty_state() -> WizardUIViewState:
    return WizardUIView(sections=[], automation=[], enabled=False).snapshot()


__all__ = [
    "configure_tables",
    "render_activity",
    "render_automation",
    "render_conditional",
    "render_sections",
    "empty_state",
]
