from __future__ import annotations

from collections.abc import Sequence

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..state import PromptMeta, SectionStatus
from . import configured_badge, dependency_badge, status_badge


def section_card(section: SectionStatus, *, expanded: bool) -> Panel:
    """Renderable accordion-style card for a wizard section."""

    detail = _detail_text(section)
    dependency_block = _dependency_block(section.prompts, expanded=expanded)
    body_segments: list[RenderableType] = [detail]
    if dependency_block is not None:
        body_segments.append(dependency_block)
    body = Group(*body_segments)
    border_style = "cyan" if expanded else "#555555"
    subtitle = status_badge(section.state)
    title = Text.assemble(
        (f"{section.order}. ", "bold"),
        (section.label, "bold"),
    )
    return Panel(
        body,
        title=title,
        subtitle=subtitle,
        subtitle_align="right",
        border_style=border_style,
        padding=(1, 2),
    )


def _detail_text(section: SectionStatus) -> Text:
    if section.detail:
        return Text(section.detail)
    return Text("No additional detail yet.", style="dim")


def _dependency_block(prompts: Sequence[PromptMeta] | None, *, expanded: bool):
    if not prompts:
        return None
    conditional_prompts = [prompt for prompt in prompts if prompt.dependencies]
    if not conditional_prompts:
        return None
    if not expanded:
        configured = sum(1 for prompt in conditional_prompts if prompt.configured)
        return Text(
            f"{configured}/{len(conditional_prompts)} conditional prompt(s) configured",
            style="section.subtitle",
        )
    table = Table.grid(padding=(0, 1))
    table.add_column("Prompt", style="bold", ratio=2)
    table.add_column("Configured", width=10)
    table.add_column("Dependencies", ratio=3)
    for prompt in conditional_prompts:
        badges = Text()
        for dependency in prompt.dependencies:
            if badges:
                badges.append(" ")
            badges.append_text(dependency_badge(dependency.label, dependency.satisfied))
        table.add_row(
            prompt.label,
            configured_badge(prompt.configured),
            badges if badges else Text("—", style="#555555"),
        )
    return Panel(
        table,
        title="Conditional prompts",
        border_style="magenta",
        padding=(0, 1),
    )


__all__ = ["section_card"]
