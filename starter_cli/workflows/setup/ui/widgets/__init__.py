from __future__ import annotations

from rich.progress_bar import ProgressBar
from rich.text import Text

STATUS_STYLES: dict[str, tuple[str, str]] = {
    "pending": ("PENDING", "#808080"),
    "running": ("RUN", "yellow"),
    "done": ("DONE", "green"),
    "failed": ("FAIL", "red"),
    "skipped": ("SKIP", "bright_black"),
    "blocked": ("BLOCK", "magenta"),
    "disabled": ("OFF", "#757575"),
}


def status_badge(state: str) -> Text:
    label, style = STATUS_STYLES.get(state, (state.upper(), "white"))
    return Text(label, style=style, justify="center")


def progress_bar(completed: int, total: int) -> ProgressBar:
    total = max(total, 1)
    completed = min(max(completed, 0), total)
    bar = ProgressBar(total=total, completed=completed)
    bar.complete_style = "green"
    bar.finished_style = "green"
    bar.pulse_style = "yellow"
    return bar


def progress_caption(
    *,
    completed: int,
    total: int,
    current_label: str | None,
    elapsed: str,
) -> Text:
    text = Text()
    text.append(f"{completed}/{total} sections complete", style="bold")
    if elapsed:
        text.append(f" • {elapsed}", style="section.subtitle")
    if current_label:
        text.append(f" • Current: {current_label}", style="section.subtitle")
    return text


def dependency_badge(label: str, satisfied: bool) -> Text:
    style = "bold green" if satisfied else "bold red"
    return Text(f"[{label}]", style=style)


def configured_badge(configured: bool) -> Text:
    if configured:
        return Text("✔", style="bold green")
    return Text("—", style="#666666")


__all__ = [
    "progress_bar",
    "progress_caption",
    "status_badge",
    "dependency_badge",
    "configured_badge",
]
