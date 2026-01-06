from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from starter_console.workflows.setup.automation import AutomationPhase
from starter_console.workflows.setup.inputs import ParsedAnswers


@dataclass(slots=True)
class WizardLaunchConfig:
    profile: str | None = None
    profiles_path: Path | None = None
    output_format: str = "summary"
    answers: ParsedAnswers = field(default_factory=dict)
    summary_path: Path | None = None
    markdown_summary_path: Path | None = None
    export_answers_path: Path | None = None
    automation_overrides: dict[AutomationPhase, bool | None] = field(default_factory=dict)
    auto_start: bool = False


@dataclass(slots=True)
class ProfileOption:
    profile_id: str
    label: str
    description: str | None
    widget_id: str


__all__ = ["ProfileOption", "WizardLaunchConfig"]
