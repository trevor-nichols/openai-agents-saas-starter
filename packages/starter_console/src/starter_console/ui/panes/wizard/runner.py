from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from starter_console.core import CLIContext
from starter_console.core.profiles import (
    load_frontend_env,
    load_profile_registry,
    select_profile,
    write_profile_manifest,
)
from starter_console.workflows.setup import SetupWizard
from starter_console.workflows.setup.automation import AutomationPhase
from starter_console.workflows.setup.inputs import HeadlessInputProvider, ParsedAnswers

from .paths import ensure_summary_paths


@dataclass(slots=True)
class WizardHeadlessRun:
    profile: str
    profiles_path: Path | None
    output_format: str
    summary_path: Path | None
    markdown_summary_path: Path | None
    export_answers_path: Path | None
    automation_overrides: dict[AutomationPhase, bool | None]
    answers: ParsedAnswers
    strict: bool
    mode: str

    @property
    def report_only(self) -> bool:
        return self.mode == "report-only"

    @property
    def non_interactive(self) -> bool:
        return self.mode == "headless" or self.strict


class WizardRunService:
    def build_runner(self, run: WizardHeadlessRun) -> Callable[[CLIContext], str]:
        def _runner(ctx: CLIContext) -> str:
            input_provider = None
            if run.non_interactive and not run.report_only:
                input_provider = HeadlessInputProvider(run.answers)
            registry = load_profile_registry(
                project_root=ctx.project_root,
                override_path=run.profiles_path,
            )
            selection = select_profile(registry, explicit=run.profile)
            frontend_env = load_frontend_env(project_root=ctx.project_root)
            write_profile_manifest(
                selection,
                project_root=ctx.project_root,
                frontend_env=frontend_env,
            )
            wizard = SetupWizard(
                ctx=ctx,
                profile=selection.profile.profile_id,
                profile_policy=selection.profile,
                output_format=run.output_format,
                input_provider=input_provider,
                summary_path=run.summary_path,
                markdown_summary_path=run.markdown_summary_path,
                export_answers_path=run.export_answers_path,
                automation_overrides=run.automation_overrides,
                enable_tui=False,
            )
            if not run.report_only:
                if wizard.summary_path is None or wizard.markdown_summary_path is None:
                    summary_path, markdown_path = ensure_summary_paths(
                        ctx, wizard.summary_path, wizard.markdown_summary_path
                    )
                    wizard.summary_path = summary_path
                    wizard.markdown_summary_path = markdown_path
                wizard.execute()
            else:
                wizard.render_report()
            summary_display = str(wizard.summary_path) if wizard.summary_path else "n/a"
            return f"Wizard complete. Summary: {summary_display}"

        return _runner


__all__ = ["WizardHeadlessRun", "WizardRunService"]
