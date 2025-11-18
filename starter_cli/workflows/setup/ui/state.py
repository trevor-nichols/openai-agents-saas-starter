from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Sequence

from ..automation import AutomationStatus
from ..schema import Condition


@dataclass(slots=True)
class DependencyStatus:
    label: str
    satisfied: bool = False


@dataclass(slots=True)
class PromptMeta:
    """Describe a prompt surfaced inside a wizard section."""

    key: str
    label: str
    description: str | None = None
    conditions: tuple[Condition, ...] = ()
    dependency_labels: tuple[str, ...] = ()
    dependencies: tuple[DependencyStatus, ...] = ()
    configured: bool = False


@dataclass(slots=True)
class SectionStatus:
    """Represents the live status for a wizard section."""

    key: str
    label: str
    order: int
    state: str = "pending"
    detail: str = ""
    prompts: Sequence[PromptMeta] = ()


@dataclass(slots=True)
class AutomationRow:
    """Represents the live status for an automation phase."""

    key: str
    label: str
    state: str = "pending"
    detail: str = ""


@dataclass(slots=True)
class WizardUIViewState:
    """Snapshot of runtime data needed to render the wizard UI."""

    sections: Sequence[SectionStatus]
    automation: Sequence[AutomationRow]
    events: Sequence[tuple[str, str]]
    current_section_key: str | None
    started_at: float | None
    expanded_sections: frozenset[str]

    @property
    def completed_sections(self) -> int:
        return sum(1 for section in self.sections if section.state == "done")

    @property
    def total_sections(self) -> int:
        return len(self.sections)

    def elapsed_text(self) -> str:
        """Human friendly elapsed timer for the wizard session."""

        if self.started_at is None:
            return ""
        elapsed = int(perf_counter() - self.started_at)
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}h {minutes:02d}m elapsed"
        if minutes:
            return f"{minutes}m {seconds:02d}s elapsed"
        return f"{seconds}s elapsed"


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


__all__ = [
    "AutomationRow",
    "DependencyStatus",
    "PromptMeta",
    "SectionStatus",
    "WizardUIViewState",
    "automation_status_to_state",
]
