from __future__ import annotations

from dataclasses import replace

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Input, OptionList, ProgressBar, RadioSet, Static

from starter_console.core import CLIContext, CLIError
from starter_console.core.profiles import load_profile_registry, select_profile
from starter_console.ui.action_runner import ActionResult, ActionRunner
from starter_console.ui.prompt_controller import PromptController

from .controls import WizardControls, build_profile_options
from .layout import compose_wizard_layout
from .models import WizardLaunchConfig
from .renderer import (
    configure_tables,
    empty_state,
    render_activity,
    render_automation,
    render_conditional,
    render_sections,
)
from .runner import WizardHeadlessRun, WizardRunService
from .session import WizardSession


class WizardPane(Vertical):
    def __init__(self, ctx: CLIContext, *, config: WizardLaunchConfig | None = None) -> None:
        super().__init__(id="wizard", classes="section-pane")
        self._ctx = ctx
        self._config = config or WizardLaunchConfig()
        self._profile_registry = load_profile_registry(
            project_root=ctx.project_root,
            override_path=self._config.profiles_path,
        )
        self._auto_selection = select_profile(self._profile_registry, explicit=None)
        self._profile_options = build_profile_options(self._profile_registry)
        self._controls = WizardControls(
            self,
            self._config,
            ctx=self._ctx,
            profile_registry=self._profile_registry,
            auto_selection=self._auto_selection,
            profile_options=self._profile_options,
        )
        self._session: WizardSession | None = None
        self._prompt_controller = PromptController(self, prefix="wizard")
        self._headless_runner = ActionRunner(
            ctx=self._ctx,
            on_status=self._set_headless_status,
            on_output=self._set_headless_output,
            on_complete=self._handle_headless_complete,
            on_state_change=self._set_headless_state,
        )
        self._runner = WizardRunService()

    def compose(self) -> ComposeResult:
        yield from compose_wizard_layout(self._profile_options)

    def on_mount(self) -> None:
        self._controls.configure_profile()
        self._controls.configure_presets()
        self._controls.update_summary_preview()
        state = self._session.state.snapshot() if self._session else empty_state()
        configure_tables(self, state)
        self._controls.configure_options()
        self._prompt_controller.set_visibility(False)
        self.set_interval(0.5, self._refresh_view)
        self.set_interval(0.2, self._poll_prompt)
        self.set_interval(0.4, self._headless_runner.refresh_output)
        if self._config.auto_start:
            self._start_wizard()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "wizard-start":
            self._start_wizard()
        elif event.button.id == "wizard-submit":
            self._prompt_controller.submit_current()
        elif event.button.id == "wizard-clear":
            self._prompt_controller.clear_input()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "wizard-input":
            self._prompt_controller.submit_current()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "wizard-options":
            self._prompt_controller.submit_choice(event.option_index)
            return
        self._controls.update_profile_context()
        self._controls.update_summary_preview()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id in {
            "wizard-profile",
            "wizard-preset",
            "wizard-cloud",
            "wizard-advanced",
        }:
            self._controls.sync_preset_controls()
            if not self._session:
                self._controls.update_profile_context()
                self._controls.update_summary_preview()

    # ------------------------------------------------------------------
    # Wizard lifecycle
    # ------------------------------------------------------------------
    def _start_wizard(self) -> None:
        if self._session and self._session.running:
            return
        if self._headless_runner.running:
            self._set_headless_status("Headless run already in progress.")
            return

        mode = self._controls.selected_mode()
        strict = self._controls.strict_enabled()
        if strict and self._controls.selected_profile() != "production":
            self._set_headless_status("--strict requires production profile.")
            return

        if mode == "interactive" and not strict:
            config = replace(self._config, profile=self._controls.selected_profile())
            config.output_format = self._controls.selected_output_format()
            config.summary_path = self._controls.path_value("wizard-summary-path")
            config.markdown_summary_path = self._controls.path_value("wizard-markdown-summary-path")
            config.export_answers_path = self._controls.path_value("wizard-export-answers")
            config.answers = self._controls.merged_answers(
                config.answers,
                on_error=self._set_headless_status,
            )
            config.automation_overrides = self._controls.automation_overrides()
            self._session = WizardSession(self._ctx, config)
            self._prompt_controller.set_channel(self._session.prompt_channel)
            self._session.start()
            self._prompt_controller.set_status("Wizard running. Awaiting prompts...")
            return

        self._start_headless(strict=strict, mode=mode)

    # ------------------------------------------------------------------
    # UI updates
    # ------------------------------------------------------------------
    def _refresh_view(self) -> None:
        if not self._session:
            return
        state = self._session.state.snapshot()
        summary = f"{state.completed_sections}/{state.total_sections} sections complete"
        if state.current_section_key:
            summary += f" | Current: {state.current_section_key}"
        elapsed = state.elapsed_text()
        if elapsed:
            summary += f" | {elapsed}"
        summary += self._controls.build_setup_summary()
        self.query_one("#wizard-summary", Static).update(summary)
        progress = self.query_one("#wizard-progress", ProgressBar)
        progress.update(total=state.total_sections, progress=state.completed_sections)
        render_sections(self, state.sections)
        render_automation(self, state.automation)
        render_conditional(self, state)
        render_activity(self, state.events)
        if self._session.done:
            self._prompt_controller.set_status("Wizard complete.")

    def _poll_prompt(self) -> None:
        if not self._session:
            return
        self._prompt_controller.poll()

    def submit_current_prompt(self, value: str | None = None) -> None:
        request = self._prompt_controller.state.current
        if not request:
            return
        if value is not None and request.kind in {"string", "secret"}:
            input_field = self.query_one("#wizard-input", Input)
            input_field.value = value
        self._prompt_controller.submit_current()

    # ------------------------------------------------------------------
    # Headless runner
    # ------------------------------------------------------------------
    def _start_headless(self, *, strict: bool, mode: str) -> None:
        try:
            answers = self._controls.load_answers()
        except CLIError as exc:
            self._set_headless_status(str(exc))
            return
        if strict and not answers:
            self._set_headless_status("--strict requires answers via files or overrides.")
            return

        run = WizardHeadlessRun(
            profile=self._controls.selected_profile(),
            profiles_path=self._config.profiles_path,
            output_format=self._controls.selected_output_format(),
            summary_path=self._controls.path_value("wizard-summary-path"),
            markdown_summary_path=self._controls.path_value("wizard-markdown-summary-path"),
            export_answers_path=self._controls.path_value("wizard-export-answers"),
            automation_overrides=self._controls.automation_overrides(),
            answers=answers,
            strict=strict,
            mode=mode,
        )

        if not self._headless_runner.start("Wizard (headless)", self._runner.build_runner(run)):
            self._set_headless_status("Headless run already active.")

    def _set_headless_status(self, message: str) -> None:
        self.query_one("#wizard-status", Static).update(message)

    def _set_headless_output(self, message: str) -> None:
        self.query_one("#wizard-output", Static).update(message)

    def _set_headless_state(self, running: bool) -> None:
        self.query_one("#wizard-start", Button).disabled = running

    def _handle_headless_complete(self, result: ActionResult[str]) -> None:
        if result.error is None and result.value:
            self._set_headless_output(result.value)


__all__ = ["WizardLaunchConfig", "WizardPane"]
