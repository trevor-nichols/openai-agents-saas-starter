from __future__ import annotations

import threading
from collections import OrderedDict, deque
from collections.abc import Mapping, Sequence
from datetime import datetime
from time import perf_counter

from ..schema import ValueLookup
from .state import (
    AutomationRow,
    DependencyStatus,
    PromptMeta,
    SectionStatus,
    WizardUIViewState,
)


class WizardUIView:
    """Thread-safe state store for the setup wizard UI."""

    def __init__(
        self,
        *,
        sections: list[tuple[str, str]],
        automation: list[tuple[str, str]],
        section_prompts: Mapping[str, Sequence[PromptMeta]] | None = None,
        enabled: bool = True,
    ) -> None:
        self.enabled = enabled
        self._lock = threading.Lock()
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
        self._started_at: float | None = None
        self._current_section: str | None = None
        self._expanded_sections: set[str] = set()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._started_at = perf_counter()
            self._append_event("Wizard initialized.")

    def stop(self) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._append_event("Wizard complete.")

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------
    def mark_section(self, key: str, state: str, detail: str | None = None) -> None:
        if not self.enabled:
            return
        with self._lock:
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

    def mark_automation(self, key: str, state: str, detail: str | None = None) -> None:
        if not self.enabled:
            return
        with self._lock:
            target = self.automation.get(key)
            if not target:
                return
            target.state = state
            if detail is not None:
                target.detail = detail

    def log(self, message: str) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._append_event(message)

    # ------------------------------------------------------------------
    # User controls
    # ------------------------------------------------------------------
    def expand_section(self, key: str) -> None:
        if not self.enabled:
            return
        with self._lock:
            if key in self.sections:
                self._expanded_sections.add(key)

    def collapse_section(self, key: str) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._expanded_sections.discard(key)

    def toggle_section(self, key: str) -> None:
        if not self.enabled:
            return
        with self._lock:
            if key not in self.sections:
                return
            if key in self._expanded_sections:
                self._expanded_sections.discard(key)
            else:
                self._expanded_sections.add(key)

    def sync_prompt_states(self, values: Mapping[str, str]) -> None:
        if not self.enabled or not self.sections:
            return
        normalized = {key.upper(): value for key, value in values.items() if isinstance(key, str)}
        lookup = ValueLookup([normalized])
        with self._lock:
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

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------
    def snapshot(self) -> WizardUIViewState:
        with self._lock:
            return WizardUIViewState(
                sections=list(self.sections.values()),
                automation=list(self.automation.values()),
                events=list(self.events),
                current_section_key=self._current_section,
                started_at=self._started_at,
                expanded_sections=frozenset(self._expanded_sections),
            )

    def _append_event(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events.appendleft((timestamp, message))


__all__ = ["WizardUIView"]
