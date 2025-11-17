"""Rich-powered status board for the setup wizard."""

from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .automation import AutomationStatus


@dataclass(slots=True)
class _Status:
    label: str
    state: str = "pending"
    detail: str = ""


class WizardUIView:
    def __init__(
        self,
        *,
        sections: list[tuple[str, str]],
        automation: list[tuple[str, str]],
        enabled: bool = True,
        console: Console | None = None,
    ) -> None:
        self.enabled = enabled
        self.console = console or Console()
        self.sections = OrderedDict((key, _Status(label=label)) for key, label in sections)
        self.automation = OrderedDict((key, _Status(label=label)) for key, label in automation)
        self.events: deque[str] = deque(maxlen=8)
        self._rendered = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        if not self.enabled:
            return
        self.log("Wizard initialized.")
        self._render()

    def stop(self) -> None:
        if not self.enabled or not self._rendered:
            return
        self.console.print(Rule("Wizard complete"))

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------
    def mark_section(self, key: str, state: str, detail: str | None = None) -> None:
        target = self.sections.get(key)
        if not target:
            return
        target.state = state
        if detail is not None:
            target.detail = detail
        self._render()

    def mark_automation(self, key: str, state: str, detail: str | None = None) -> None:
        target = self.automation.get(key)
        if not target:
            return
        target.state = state
        if detail is not None:
            target.detail = detail
        self._render()

    def log(self, message: str) -> None:
        self.events.appendleft(message)
        self._render()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _render(self) -> None:
        if not self.enabled:
            return
        self.console.print(Rule("Starter CLI Wizard Dashboard"))
        self.console.print(self._build_sections_table())
        self.console.print(self._build_automation_table())
        self.console.print(self._build_log_panel())
        self._rendered = True

    def _build_sections_table(self) -> Table:
        table = Table(title="Milestones", box=None)
        table.add_column("Status", no_wrap=True)
        table.add_column("Section")
        table.add_column("Detail")
        for status in self.sections.values():
            table.add_row(
                self._badge(status.state),
                status.label,
                status.detail or "",
            )
        return table

    def _build_automation_table(self) -> Table:
        table = Table(title="Automation", box=None)
        table.add_column("Status", no_wrap=True)
        table.add_column("Phase")
        table.add_column("Detail")
        for status in self.automation.values():
            table.add_row(
                self._badge(status.state),
                status.label,
                status.detail or "",
            )
        return table

    def _build_log_panel(self) -> Panel:
        if not self.events:
            body = Text("No activity yet.")
        else:
            body = Text("\n").join(Text(f"- {event}") for event in self.events)
        return Panel(body, title="Activity", border_style="cyan")

    @staticmethod
    def _badge(state: str) -> Text:
        styles = {
            "pending": ("PENDING", "grey50"),
            "running": ("RUN", "yellow"),
            "done": ("DONE", "green"),
            "failed": ("FAIL", "red"),
            "skipped": ("SKIP", "bright_black"),
            "blocked": ("BLOCK", "magenta"),
            "disabled": ("OFF", "grey46"),
        }
        label, style = styles.get(state, (state.upper(), "white"))
        return Text(label, style=style, justify="center")


def automation_status_to_state(status: AutomationStatus) -> str:
    mapping = {
        AutomationStatus.DISABLED: "disabled",
        AutomationStatus.PENDING: "pending",
        AutomationStatus.RUNNING: "running",
        AutomationStatus.SUCCEEDED: "done",
        AutomationStatus.FAILED: "failed",
        AutomationStatus.SKIPPED: "skipped",
        AutomationStatus.BLOCKED: "blocked",
    }
    return mapping.get(status, "pending")


__all__ = ["WizardUIView", "automation_status_to_state"]
