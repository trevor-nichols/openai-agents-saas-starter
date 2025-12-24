from __future__ import annotations

import io
import threading
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    DataTable,
    Input,
    OptionList,
    ProgressBar,
    RadioButton,
    RadioSet,
    Static,
)

from starter_cli.core import CLIContext
from starter_cli.ports.presentation import NotifyPort
from starter_cli.presenters import PresenterConsoleAdapter, build_textual_presenter
from starter_cli.ui.context import derive_presenter_context
from starter_cli.ui.prompt_controller import PromptController
from starter_cli.ui.prompting import PromptChannel, TextualPromptPort
from starter_cli.workflows.setup import SetupWizard
from starter_cli.workflows.setup.automation import AutomationPhase
from starter_cli.workflows.setup.inputs import ParsedAnswers
from starter_cli.workflows.setup.schema import load_schema
from starter_cli.workflows.setup.section_specs import SECTION_SPECS
from starter_cli.workflows.setup.ui import WizardUIView
from starter_cli.workflows.setup.ui.schema_metadata import build_section_prompt_metadata
from starter_cli.workflows.setup.ui.state import AutomationRow, SectionStatus, WizardUIViewState
from starter_cli.workflows.setup.wizard import PROFILE_CHOICES, build_automation_labels


@dataclass(slots=True)
class WizardLaunchConfig:
    profile: str = "demo"
    output_format: str = "summary"
    answers: ParsedAnswers = field(default_factory=dict)
    summary_path: Path | None = None
    markdown_summary_path: Path | None = None
    export_answers_path: Path | None = None
    automation_overrides: dict[AutomationPhase, bool | None] = field(default_factory=dict)
    enable_schema: bool = True
    auto_start: bool = False



class WizardNotifyPort(NotifyPort):
    def __init__(self, ui: WizardUIView) -> None:
        self._ui = ui
        self.stream = io.StringIO()
        self.err_stream = io.StringIO()

    def info(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._log("INFO", message, topic)

    def warn(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._log("WARN", message, topic)

    def error(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._log("ERROR", message, topic)

    def success(self, message: str, topic: str | None = None, *, stream=None) -> None:
        self._log("SUCCESS", message, topic)

    def note(self, message: str, topic: str | None = None) -> None:
        self._log("NOTE", message, topic)

    def section(self, title: str, subtitle: str | None = None, *, icon: str = "*") -> None:
        line = f"{icon} {title}"
        if subtitle:
            line += f" - {subtitle}"
        self._ui.log(line)

    def step(self, prefix: str, message: str) -> None:
        self._ui.log(f"{prefix} {message}")

    def value_change(
        self,
        *,
        scope: str | None,
        key: str,
        previous: str | None,
        current: str,
        secret: bool = False,
    ) -> None:
        scope_label = f"[{scope}] " if scope else ""
        prev_display = "<unset>" if previous is None else ("***" if secret else previous)
        next_display = "***" if secret else current
        self._ui.log(f"{scope_label}{key}: {prev_display} -> {next_display}")

    def newline(self) -> None:
        self._ui.log("")

    def print(self, *renderables, **kwargs) -> None:
        joined = " ".join(str(item) for item in renderables)
        self._ui.log(joined)

    def render(self, renderable, *, error: bool = False) -> None:
        self._ui.log(str(renderable))

    def rule(self, title: str) -> None:
        self._ui.log(f"---- {title} ----")

    def _log(self, level: str, message: str, topic: str | None) -> None:
        topic_label = f"[{topic}]" if topic else ""
        self._ui.log(f"[{level}]{topic_label} {message}")


class WizardSession:
    def __init__(self, ctx: CLIContext, config: WizardLaunchConfig) -> None:
        self._ctx = ctx
        self._config = config
        self._prompt_channel = PromptChannel()
        self._thread: threading.Thread | None = None
        self._done = threading.Event()
        self.error: Exception | None = None
        self.state = self._build_state()

    @property
    def prompt_channel(self) -> PromptChannel:
        return self._prompt_channel

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def done(self) -> bool:
        return self._done.is_set()

    def start(self) -> None:
        if self.running:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _build_state(self) -> WizardUIView:
        schema = load_schema() if self._config.enable_schema else None
        section_prompts = build_section_prompt_metadata(schema)
        return WizardUIView(
            sections=[(spec.key, spec.label) for spec in SECTION_SPECS],
            automation=build_automation_labels(),
            section_prompts=section_prompts,
            enabled=True,
        )

    def _run(self) -> None:
        try:
            notify = WizardNotifyPort(self.state)
            prompt = TextualPromptPort(prefill=self._config.answers, channel=self._prompt_channel)
            presenter = build_textual_presenter(prompt=prompt, notify=notify)
            wizard_console = PresenterConsoleAdapter(presenter)
            wizard_ctx = derive_presenter_context(
                self._ctx, console=wizard_console, presenter=presenter
            )
            input_provider = prompt
            summary_path = self._config.summary_path or (
                self._ctx.project_root / "var/reports/setup-summary.json"
            )
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            markdown_path = self._config.markdown_summary_path or (
                self._ctx.project_root / "var/reports/cli-one-stop-summary.md"
            )
            markdown_path.parent.mkdir(parents=True, exist_ok=True)
            wizard = SetupWizard(
                ctx=wizard_ctx,
                profile=self._config.profile,
                output_format=self._config.output_format,
                input_provider=input_provider,
                summary_path=summary_path,
                markdown_summary_path=markdown_path,
                export_answers_path=self._config.export_answers_path,
                automation_overrides=self._config.automation_overrides,
                enable_tui=True,
                enable_schema=self._config.enable_schema,
                wizard_ui=self.state,
            )
            wizard.execute()
        except Exception as exc:  # pragma: no cover - defensive
            self.error = exc
            self.state.log(f"Wizard failed: {exc}")
        finally:
            self._done.set()



class WizardPane(Vertical):
    def __init__(self, ctx: CLIContext, *, config: WizardLaunchConfig | None = None) -> None:
        super().__init__(id="wizard", classes="section-pane")
        self._ctx = ctx
        self._config = config or WizardLaunchConfig()
        self._session: WizardSession | None = None
        self._prompt_controller = PromptController(self, prefix="wizard")

    def compose(self) -> ComposeResult:
        yield Static("Setup Wizard", classes="section-title")
        yield Static("", id="wizard-summary", classes="section-summary")
        with Horizontal(id="wizard-controls"):
            yield Static("Profile", id="wizard-profile-label", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Demo", id="profile-demo"),
                RadioButton("Staging", id="profile-staging"),
                RadioButton("Production", id="profile-production"),
                id="wizard-profile",
            )
            yield Static("Hosting", id="wizard-preset-label", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Local Docker", id="preset-local"),
                RadioButton("Cloud Managed", id="preset-cloud"),
                RadioButton("Enterprise", id="preset-enterprise"),
                id="wizard-preset",
            )
            yield Static("Cloud", id="wizard-cloud-label", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("AWS", id="cloud-aws"),
                RadioButton("Azure", id="cloud-azure"),
                RadioButton("GCP", id="cloud-gcp"),
                RadioButton("Other", id="cloud-other"),
                id="wizard-cloud",
            )
            yield Static("Advanced", id="wizard-advanced-label", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("On", id="advanced-on"),
                RadioButton("Off", id="advanced-off"),
                id="wizard-advanced",
            )
            yield Button("Start Wizard", id="wizard-start", variant="primary")
        yield ProgressBar(id="wizard-progress", total=len(SECTION_SPECS))
        with Horizontal(id="wizard-main"):
            yield DataTable(id="wizard-sections", zebra_stripes=True)
            yield DataTable(id="wizard-automation", zebra_stripes=True)
        yield DataTable(id="wizard-conditional", zebra_stripes=True)
        yield Static("", id="wizard-activity", classes="section-footnote")
        with Vertical(id="wizard-prompt"):
            yield Static("", id="wizard-prompt-label")
            yield Static("", id="wizard-prompt-detail")
            yield Input(id="wizard-input")
            yield OptionList(id="wizard-options")
            with Horizontal(id="wizard-prompt-actions"):
                yield Button("Submit", id="wizard-submit", variant="primary")
                yield Button("Clear", id="wizard-clear")
            yield Static("", id="wizard-prompt-status", classes="section-footnote")

    def on_mount(self) -> None:
        self._configure_profile()
        self._configure_presets()
        self._configure_tables()
        self._prompt_controller.set_visibility(False)
        self.set_interval(0.5, self._refresh_view)
        self.set_interval(0.2, self._poll_prompt)
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
        if event.option_list.id != "wizard-options":
            return
        self._prompt_controller.submit_choice(event.option_index)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id in {
            "wizard-profile",
            "wizard-preset",
            "wizard-cloud",
            "wizard-advanced",
        }:
            self._sync_preset_controls()
            if not self._session:
                self._update_summary_preview()

    # ------------------------------------------------------------------
    # Wizard lifecycle
    # ------------------------------------------------------------------
    def _start_wizard(self) -> None:
        if self._session and self._session.running:
            return
        config = replace(self._config, profile=self._selected_profile())
        config.answers = self._merged_answers(config.answers)
        self._session = WizardSession(self._ctx, config)
        self._prompt_controller.set_channel(self._session.prompt_channel)
        self._session.start()
        self._prompt_controller.set_status("Wizard running. Awaiting prompts...")

    def _selected_profile(self) -> str:
        profiles = {
            "profile-demo": "demo",
            "profile-staging": "staging",
            "profile-production": "production",
        }
        radio = self.query_one("#wizard-profile", RadioSet)
        selected = radio.pressed_button
        if selected is None:
            return self._config.profile
        return profiles.get(selected.id or "", self._config.profile)

    def _selected_preset(self) -> str:
        presets = {
            "preset-local": "local_docker",
            "preset-cloud": "cloud_managed",
            "preset-enterprise": "enterprise_custom",
        }
        radio = self.query_one("#wizard-preset", RadioSet)
        selected = radio.pressed_button
        if selected is None:
            return self._default_preset()
        return presets.get(selected.id or "", self._default_preset())

    def _selected_cloud(self) -> str:
        clouds = {
            "cloud-aws": "aws",
            "cloud-azure": "azure",
            "cloud-gcp": "gcp",
            "cloud-other": "other",
        }
        radio = self.query_one("#wizard-cloud", RadioSet)
        selected = radio.pressed_button
        if selected is None:
            return self._default_cloud()
        return clouds.get(selected.id or "", self._default_cloud())

    def _selected_advanced(self) -> bool:
        radio = self.query_one("#wizard-advanced", RadioSet)
        selected = radio.pressed_button
        if selected is None:
            return self._default_advanced()
        return (selected.id or "") == "advanced-on"

    def _merged_answers(self, base_answers: ParsedAnswers) -> ParsedAnswers:
        answers = dict(base_answers)
        preset = self._selected_preset()
        answers.setdefault("SETUP_HOSTING_PRESET", preset)
        answers.setdefault("SETUP_CLOUD_PROVIDER", self._selected_cloud())
        answers.setdefault("SETUP_SHOW_ADVANCED", "true" if self._selected_advanced() else "false")
        return answers

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
        summary += self._build_setup_summary()
        self.query_one("#wizard-summary", Static).update(summary)
        progress = self.query_one("#wizard-progress", ProgressBar)
        progress.update(total=state.total_sections, progress=state.completed_sections)
        self._render_sections(state.sections)
        self._render_automation(state.automation)
        self._render_conditional(state)
        self._render_activity(state.events)
        if self._session.done:
            self._prompt_controller.set_status("Wizard complete.")

    def _render_sections(self, sections: Iterable[SectionStatus]) -> None:
        table = self.query_one("#wizard-sections", DataTable)
        table.clear(columns=True)
        table.add_columns("#", "Section", "Status", "Detail")
        for section in sections:
            table.add_row(
                str(section.order),
                section.label,
                section.state,
                section.detail or "",
            )

    def _render_automation(self, automation: Iterable[AutomationRow]) -> None:
        table = self.query_one("#wizard-automation", DataTable)
        table.clear(columns=True)
        table.add_columns("Status", "Phase", "Detail")
        for row in automation:
            table.add_row(row.state, row.label, row.detail or "")

    def _render_conditional(self, state: WizardUIViewState) -> None:
        table = self.query_one("#wizard-conditional", DataTable)
        table.clear(columns=True)
        table.add_columns("Prompt", "Configured", "Dependencies")
        current = None
        if state.current_section_key:
            current = next(
                (section for section in state.sections if section.key == state.current_section_key),
                None,
            )
        if not current:
            table.add_row("-", "-", "No active section")
            return
        prompts = [prompt for prompt in current.prompts if prompt.dependencies]
        if not prompts:
            table.add_row("-", "-", "No conditional prompts")
            return
        for prompt in prompts:
            deps = ", ".join(
                f"{dep.label}={'ok' if dep.satisfied else 'no'}"
                for dep in prompt.dependencies
            )
            table.add_row(prompt.label, "yes" if prompt.configured else "no", deps)

    def _render_activity(self, events: Iterable[tuple[str, str]]) -> None:
        lines = [f"{timestamp} {message}" for timestamp, message in events]
        self.query_one("#wizard-activity", Static).update("\n".join(lines))

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

    def _configure_tables(self) -> None:
        self._render_sections([])
        self._render_automation([])
        self._render_conditional(
            self._session.state.snapshot() if self._session else _empty_state()
        )

    def _configure_profile(self) -> None:
        profile = self._config.profile
        if profile not in PROFILE_CHOICES:
            profile = "demo"
        selection = {
            "demo": "profile-demo",
            "staging": "profile-staging",
            "production": "profile-production",
        }[profile]
        button = self.query_one(f"#{selection}", RadioButton)
        button.value = True
        self._update_summary_preview()

    def _configure_presets(self) -> None:
        preset = self._config.answers.get("SETUP_HOSTING_PRESET") if self._config.answers else None
        if not preset:
            preset = self._default_preset()
        preset_id = {
            "local_docker": "preset-local",
            "cloud_managed": "preset-cloud",
            "enterprise_custom": "preset-enterprise",
        }.get(preset, "preset-local")
        self.query_one(f"#{preset_id}", RadioButton).value = True

        cloud = self._config.answers.get("SETUP_CLOUD_PROVIDER") if self._config.answers else None
        if not cloud:
            cloud = self._default_cloud()
        cloud_id = {
            "aws": "cloud-aws",
            "azure": "cloud-azure",
            "gcp": "cloud-gcp",
            "other": "cloud-other",
        }.get(cloud, "cloud-aws")
        self.query_one(f"#{cloud_id}", RadioButton).value = True

        advanced = self._config.answers.get("SETUP_SHOW_ADVANCED") if self._config.answers else None
        is_advanced = self._default_advanced()
        if advanced is not None:
            is_advanced = advanced.lower() in {"1", "true", "yes", "y"}
        advanced_id = "advanced-on" if is_advanced else "advanced-off"
        self.query_one(f"#{advanced_id}", RadioButton).value = True
        self._sync_preset_controls()

    def _default_preset(self) -> str:
        return "local_docker" if self._config.profile == "demo" else "cloud_managed"

    def _default_cloud(self) -> str:
        return "aws"

    def _default_advanced(self) -> bool:
        return self._config.profile in {"staging", "production"}

    def _sync_preset_controls(self) -> None:
        preset = self._selected_preset()
        cloud_label = self.query_one("#wizard-cloud-label", Static)
        cloud_radio = self.query_one("#wizard-cloud", RadioSet)
        is_cloud = preset == "cloud_managed"
        cloud_label.display = is_cloud
        cloud_radio.display = is_cloud
        if not is_cloud:
            default_cloud = self._default_cloud()
            cloud_id = {
                "aws": "cloud-aws",
                "azure": "cloud-azure",
                "gcp": "cloud-gcp",
                "other": "cloud-other",
            }[default_cloud]
            self.query_one(f"#{cloud_id}", RadioButton).value = True

    def _build_setup_summary(self) -> str:
        preset = self._selected_preset()
        advanced = "on" if self._selected_advanced() else "off"
        summary = f" | Preset: {preset}"
        if preset == "cloud_managed":
            summary += f" ({self._selected_cloud()})"
        summary += f" | Advanced: {advanced}"
        return summary

    def _update_summary_preview(self) -> None:
        summary = f"Preset: {self._selected_preset()}"
        if self._selected_preset() == "cloud_managed":
            summary += f" ({self._selected_cloud()})"
        summary += f" | Advanced: {'on' if self._selected_advanced() else 'off'}"
        self.query_one("#wizard-summary", Static).update(summary)


def _empty_state():
    return WizardUIView(sections=[], automation=[], enabled=False).snapshot()


__all__ = ["WizardLaunchConfig", "WizardPane"]
