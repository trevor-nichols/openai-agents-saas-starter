from __future__ import annotations

import shlex

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, OptionList, RadioButton, RadioSet, Static, Switch

from starter_console.core import CLIContext
from starter_console.services.secrets.onboard import SecretsOnboardConfig, run_secrets_onboard
from starter_console.ui.prompt_controller import PromptController
from starter_console.ui.workflow_runner import WorkflowResult, WorkflowRunner
from starter_console.workflows.secrets import registry
from starter_console.workflows.secrets.models import OnboardResult


class SecretsOnboardPane(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="secrets", classes="section-pane")
        self.ctx = ctx
        self._options = list(registry.provider_options())
        self._prompt_controller = PromptController(self, prefix="secrets")
        self._runner: WorkflowRunner[OnboardResult] = WorkflowRunner(
            ctx=self.ctx,
            prompt_controller=self._prompt_controller,
            on_status=self._set_status,
            on_output=self._set_output,
            on_complete=self._handle_complete,
            on_state_change=self._set_action_state,
        )

    def compose(self) -> ComposeResult:
        yield Static("Secrets Onboarding", classes="section-title")
        yield Static(
            "Configure secrets/signing providers and export env updates.",
            classes="section-description",
        )
        with Horizontal(classes="ops-actions"):
            yield Static("Provider", classes="wizard-control-label")
            yield RadioSet(
                *[
                    RadioButton(option.label, id=f"secrets-provider-{option.literal.value}")
                    for option in self._options
                ],
                id="secrets-provider",
            )
            yield Button("Run Onboarding", id="secrets-run", variant="primary")
        yield Static("", id="secrets-provider-detail", classes="section-summary")
        with Horizontal(classes="ops-actions"):
            yield Static("Non-interactive", classes="wizard-control-label")
            yield Switch(value=False, id="secrets-non-interactive")
            yield Static("Skip automation", classes="wizard-control-label")
            yield Switch(value=False, id="secrets-skip-automation")
        with Horizontal(classes="ops-actions"):
            yield Static("Answers files", classes="wizard-control-label")
            yield Input(
                id="secrets-answers-files",
                placeholder="answers.json, /path/to/answers.json",
            )
        with Horizontal(classes="ops-actions"):
            yield Static("Var overrides", classes="wizard-control-label")
            yield Input(
                id="secrets-var-overrides",
                placeholder="KEY=VALUE, NEXT_KEY=VALUE",
            )
        yield Static("", id="secrets-summary", classes="section-summary")
        yield Static("", id="secrets-output", classes="ops-output")
        with Vertical(id="secrets-prompt"):
            yield Static("", id="secrets-prompt-label")
            yield Static("", id="secrets-prompt-detail")
            yield Input(id="secrets-input")
            yield OptionList(id="secrets-options")
            with Horizontal(id="secrets-prompt-actions"):
                yield Button("Submit", id="secrets-submit", variant="primary")
                yield Button("Clear", id="secrets-clear")
            yield Static("", id="secrets-prompt-status", classes="section-footnote")
        yield Static("", id="secrets-status", classes="section-footnote")

    def on_mount(self) -> None:
        self._configure_defaults()
        self._prompt_controller.set_visibility(False)
        self.set_interval(0.2, self._runner.poll_prompt)
        self.set_interval(0.4, self._runner.refresh_output)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "secrets-run":
            self._start_onboard()
        elif event.button.id == "secrets-submit":
            self._prompt_controller.submit_current()
        elif event.button.id == "secrets-clear":
            self._prompt_controller.clear_input()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "secrets-input":
            self._prompt_controller.submit_current()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "secrets-options":
            return
        self._prompt_controller.submit_choice(event.option_index)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "secrets-provider":
            self._update_provider_detail()

    def _configure_defaults(self) -> None:
        if not self._options:
            return
        default = self._options[0]
        button = self.query_one(f"#secrets-provider-{default.literal.value}", RadioButton)
        button.value = True
        self._update_provider_detail()

    def _start_onboard(self) -> None:
        provider = self._selected_provider()
        non_interactive = self.query_one("#secrets-non-interactive", Switch).value
        skip_automation = self.query_one("#secrets-skip-automation", Switch).value
        answers_files = self._parse_tokens(self.query_one("#secrets-answers-files", Input).value)
        overrides = self._parse_tokens(self.query_one("#secrets-var-overrides", Input).value)

        config = SecretsOnboardConfig(
            provider=provider,
            non_interactive=non_interactive,
            answers_files=answers_files,
            overrides=overrides,
            skip_automation=skip_automation,
        )

        def _runner(ctx: CLIContext) -> OnboardResult:
            return run_secrets_onboard(ctx, config)

        if not self._runner.start("Secrets onboarding", _runner):
            self._set_status("Secrets onboarding already running.")

    def _handle_complete(self, result: WorkflowResult[OnboardResult]) -> None:
        if result.error or result.value is None:
            return
        value = result.value
        provider = getattr(value, "provider", None)
        provider_label = provider.value if provider is not None else "unknown"
        env_updates = getattr(value, "env_updates", {}) or {}
        warnings = getattr(value, "warnings", []) or []
        artifacts = getattr(value, "artifacts", None)
        summary = (
            f"Provider: {provider_label} | Env updates: {len(env_updates)} | "
            f"Warnings: {len(warnings)}"
        )
        if artifacts:
            summary += f" | Artifacts: {len(artifacts)}"
        self.query_one("#secrets-summary", Static).update(summary)

    def _selected_provider(self) -> str | None:
        radio = self.query_one("#secrets-provider", RadioSet)
        selected = radio.pressed_button
        if not selected or not selected.id:
            return None
        return selected.id.replace("secrets-provider-", "")

    def _update_provider_detail(self) -> None:
        detail = ""
        selected = self._selected_provider()
        for option in self._options:
            if option.literal.value == selected:
                detail = option.description
                if not option.available:
                    detail = f"{detail} (coming soon)"
                break
        self.query_one("#secrets-provider-detail", Static).update(detail)

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#secrets-run", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#secrets-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#secrets-output", Static).update(message)

    @staticmethod
    def _parse_tokens(raw: str) -> list[str]:
        if not raw:
            return []
        cleaned = " ".join(raw.replace(",", " ").splitlines())
        return [token for token in shlex.split(cleaned) if token]


__all__ = ["SecretsOnboardPane"]
