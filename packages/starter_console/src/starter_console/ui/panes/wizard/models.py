from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from starter_console.workflows.setup.automation import AutomationPhase
from starter_console.workflows.setup.inputs import ParsedAnswers


@dataclass(slots=True)
class WizardLaunchConfig:
    profile: str = "demo"
    output_format: str = "summary"
    answers: ParsedAnswers = field(default_factory=dict)
    summary_path: Path | None = None
    markdown_summary_path: Path | None = None
    export_answers_path: Path | None = None
    automation_overrides: dict[AutomationPhase, bool | None] = field(default_factory=dict)
    auto_start: bool = False


__all__ = ["WizardLaunchConfig"]
