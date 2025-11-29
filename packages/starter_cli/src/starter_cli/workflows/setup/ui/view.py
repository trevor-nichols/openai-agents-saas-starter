from __future__ import annotations

from collections import OrderedDict, deque
from collections.abc import Mapping, Sequence
from datetime import datetime
from time import perf_counter

from rich.console import Console
from rich.live import Live
from rich.rule import Rule

from ..schema import ValueLookup
from .layout import build_layout
from .state import (
    AutomationRow,
    DependencyStatus,
    PromptMeta,
    SectionStatus,
    WizardUIViewState,
)


class WizardUIView:
    """Rich-powered terminal UI for the setup wizard."""

    def __init__(
        self,
        *,
        sections: list[tuple[str, str]],
        automation: list[tuple[str, str]],
        section_prompts: Mapping[str, Sequence[PromptMeta]] | None = None,
        enabled: bool = True,
        console: Console | None = None,
    ) -> None:
        self.enabled = enabled
        self.console = console or Console()
        prompts_map = section_prompts or {}
        self.sections = OrderedDict(
            (key, SectionStatus(key=key, label=label, order=index + 1))
            for index, (key, label) in enumerate(sections)
        )
        self._prompt_index: dict[str, PromptMeta] = {}
        for key, status in self.sections.items():
            prompts = tuple(prompts_map.get(key, ()))
            status.prompts = prompts
            for prompt in prompts:
                self._prompt_index[prompt.key] = prompt
        self.automation = OrderedDict(
            (key, AutomationRow(key=key, label=label))
            for key, label in automation
        )
        self.events: deque[tuple[str, str]] = deque(maxlen=8)
        self._live: Live | None = None
        self._started_at: float | None = None
        self._current_section: str | None = None
        self._expanded_sections: set[str] = set()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        if not self.enabled or self._live is not None:
            return
        self._started_at = perf_counter()
        self._live = Live(
            build_layout(self._snapshot()),
            console=self.console,
            refresh_per_second=6,
        )
        self._live.start()
        self.log("Wizard initialized.")

    def stop(self) -> None:
        if not self.enabled:
            return
        if self._live is not None:
            self._live.stop()
            self._live = None
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
        if state == "running":
            self._current_section = key
        elif self._current_section == key:
            self._current_section = None
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
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events.appendleft((timestamp, message))
        self._render()

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _render(self) -> None:
        if not self.enabled or not self._live:
            return
        self._live.update(build_layout(self._snapshot()))

    def _snapshot(self) -> WizardUIViewState:
        return WizardUIViewState(
            sections=list(self.sections.values()),
            automation=list(self.automation.values()),
            events=list(self.events),
            current_section_key=self._current_section,
            started_at=self._started_at,
            expanded_sections=frozenset(self._expanded_sections),
        )

    # ------------------------------------------------------------------
    # User controls
    # ------------------------------------------------------------------
    def expand_section(self, key: str) -> None:
        if key not in self.sections:
            return
        self._expanded_sections.add(key)
        self._render()

    def collapse_section(self, key: str) -> None:
        if key not in self.sections:
            return
        self._expanded_sections.discard(key)
        self._render()

    def toggle_section(self, key: str) -> None:
        if key not in self.sections:
            return
        if key in self._expanded_sections:
            self._expanded_sections.discard(key)
        else:
            self._expanded_sections.add(key)
        self._render()

    def sync_prompt_states(self, values: Mapping[str, str]) -> None:
        if not self.enabled or not self.sections:
            return
        normalized = {key.upper(): value for key, value in values.items() if isinstance(key, str)}
        lookup = ValueLookup([normalized])
        for status in self.sections.values():
            for prompt in status.prompts:
                prompt.configured = bool(normalized.get(prompt.key.upper()))
                updated: list[DependencyStatus] = []
                for label, condition in zip(
                    prompt.dependency_labels,
                    prompt.conditions,
                    strict=False,
                ):
                    satisfied = condition.evaluate(lookup)
                    updated.append(DependencyStatus(label=label, satisfied=satisfied))
                prompt.dependencies = tuple(updated)
        self._render()


__all__ = ["WizardUIView"]
