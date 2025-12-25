from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from textual.widgets import Input, RadioButton, RadioSet, Static, Switch

from starter_console.core import CLIError
from starter_console.workflows.setup.automation import ALL_AUTOMATION_PHASES, AutomationPhase
from starter_console.workflows.setup.inputs import (
    ParsedAnswers,
    load_answers_files,
    merge_answer_overrides,
)
from starter_console.workflows.setup.wizard import PROFILE_CHOICES

from .models import WizardLaunchConfig


class _QueryPane(Protocol):
    def query_one(self, *args: Any, **kwargs: Any) -> Any: ...


_PROFILE_OPTIONS: dict[str, str] = {
    "profile-demo": "demo",
    "profile-staging": "staging",
    "profile-production": "production",
}
_PRESET_OPTIONS: dict[str, str] = {
    "preset-local": "local_docker",
    "preset-cloud": "cloud_managed",
    "preset-enterprise": "enterprise_custom",
}
_CLOUD_OPTIONS: dict[str, str] = {
    "cloud-aws": "aws",
    "cloud-azure": "azure",
    "cloud-gcp": "gcp",
    "cloud-other": "other",
}
_OUTPUT_OPTIONS: dict[str, str] = {
    "wizard-output-summary": "summary",
    "wizard-output-json": "json",
    "wizard-output-checklist": "checklist",
}


class WizardControls:
    def __init__(self, pane: _QueryPane, config: WizardLaunchConfig) -> None:
        self._pane = pane
        self._config = config

    def configure_profile(self) -> None:
        profile = self._config.profile
        if profile not in PROFILE_CHOICES:
            profile = "demo"
        selection = self._reverse_map(_PROFILE_OPTIONS).get(profile, "profile-demo")
        button = self._pane.query_one(f"#{selection}", RadioButton)
        button.value = True
        self.update_summary_preview()

    def configure_presets(self) -> None:
        preset = self._config.answers.get("SETUP_HOSTING_PRESET") if self._config.answers else None
        if not preset:
            preset = self._default_preset()
        preset_id = self._reverse_map(_PRESET_OPTIONS).get(preset, "preset-local")
        self._pane.query_one(f"#{preset_id}", RadioButton).value = True

        cloud = self._config.answers.get("SETUP_CLOUD_PROVIDER") if self._config.answers else None
        if not cloud:
            cloud = self._default_cloud()
        cloud_id = self._reverse_map(_CLOUD_OPTIONS).get(cloud, "cloud-aws")
        self._pane.query_one(f"#{cloud_id}", RadioButton).value = True

        advanced = self._config.answers.get("SETUP_SHOW_ADVANCED") if self._config.answers else None
        is_advanced = self._default_advanced()
        if advanced is not None:
            is_advanced = advanced.lower() in {"1", "true", "yes", "y"}
        advanced_id = "advanced-on" if is_advanced else "advanced-off"
        self._pane.query_one(f"#{advanced_id}", RadioButton).value = True
        self.sync_preset_controls()

    def configure_options(self) -> None:
        self._pane.query_one("#wizard-mode-interactive", RadioButton).value = True
        output_id = self._reverse_map(_OUTPUT_OPTIONS).get(
            self._config.output_format, "wizard-output-summary"
        )
        self._pane.query_one(f"#{output_id}", RadioButton).value = True
        self._pane.query_one("#wizard-strict", Switch).value = False
        if self._config.summary_path:
            self._pane.query_one("#wizard-summary-path", Input).value = str(
                self._config.summary_path
            )
        if self._config.markdown_summary_path:
            self._pane.query_one("#wizard-markdown-summary-path", Input).value = str(
                self._config.markdown_summary_path
            )
        if self._config.export_answers_path:
            self._pane.query_one("#wizard-export-answers", Input).value = str(
                self._config.export_answers_path
            )
        for phase in ALL_AUTOMATION_PHASES:
            self._pane.query_one(f"#wizard-auto-{phase.value}", RadioButton).value = True

    def selected_profile(self) -> str:
        return self._radio_selection("wizard-profile", _PROFILE_OPTIONS, self._config.profile)

    def selected_preset(self) -> str:
        return self._radio_selection("wizard-preset", _PRESET_OPTIONS, self._default_preset())

    def selected_cloud(self) -> str:
        return self._radio_selection("wizard-cloud", _CLOUD_OPTIONS, self._default_cloud())

    def selected_advanced(self) -> bool:
        radio = self._pane.query_one("#wizard-advanced", RadioSet)
        selected = radio.pressed_button
        if selected is None:
            return self._default_advanced()
        return (selected.id or "") == "advanced-on"

    def selected_mode(self) -> str:
        radio = self._pane.query_one("#wizard-mode", RadioSet)
        selected = radio.pressed_button
        if selected is None or selected.id is None:
            return "interactive"
        if selected.id.endswith("headless"):
            return "headless"
        if selected.id.endswith("report"):
            return "report-only"
        return "interactive"

    def selected_output_format(self) -> str:
        radio = self._pane.query_one("#wizard-output-format", RadioSet)
        selected = radio.pressed_button
        if selected is None or selected.id is None:
            return self._config.output_format
        if selected.id.endswith("json"):
            return "json"
        if selected.id.endswith("checklist"):
            return "checklist"
        return "summary"

    def strict_enabled(self) -> bool:
        return self._pane.query_one("#wizard-strict", Switch).value

    def path_value(self, input_id: str) -> Path | None:
        raw = self._pane.query_one(f"#{input_id}", Input).value.strip()
        if not raw:
            return None
        return Path(raw).expanduser().resolve()

    def automation_overrides(self) -> dict[AutomationPhase, bool | None]:
        overrides: dict[AutomationPhase, bool | None] = {}
        for phase in ALL_AUTOMATION_PHASES:
            radio = self._pane.query_one(f"#wizard-automation-{phase.value}", RadioSet)
            selected = radio.pressed_button
            if selected is None or selected.id is None:
                continue
            if selected.id.endswith("auto"):
                overrides[phase] = None
            elif selected.id.endswith("on"):
                overrides[phase] = True
            elif selected.id.endswith("off"):
                overrides[phase] = False
        return overrides

    def load_answers(self) -> ParsedAnswers:
        files = self._split_tokens("wizard-answers-files")
        overrides = self._split_tokens("wizard-var-overrides")
        answers: ParsedAnswers = {}
        if files:
            answers = load_answers_files(files)
        if overrides:
            answers = merge_answer_overrides(answers, overrides)
        return answers

    def merged_answers(
        self,
        base_answers: ParsedAnswers,
        *,
        on_error: Callable[[str], None] | None = None,
    ) -> ParsedAnswers:
        answers = dict(base_answers)
        try:
            answers.update(self.load_answers())
        except CLIError as exc:
            if on_error:
                on_error(str(exc))
        preset = self.selected_preset()
        answers.setdefault("SETUP_HOSTING_PRESET", preset)
        answers.setdefault("SETUP_CLOUD_PROVIDER", self.selected_cloud())
        answers.setdefault(
            "SETUP_SHOW_ADVANCED", "true" if self.selected_advanced() else "false"
        )
        return answers

    def sync_preset_controls(self) -> None:
        preset = self.selected_preset()
        cloud_label = self._pane.query_one("#wizard-cloud-label", Static)
        cloud_radio = self._pane.query_one("#wizard-cloud", RadioSet)
        is_cloud = preset == "cloud_managed"
        cloud_label.display = is_cloud
        cloud_radio.display = is_cloud
        if not is_cloud:
            default_cloud = self._default_cloud()
            cloud_id = self._reverse_map(_CLOUD_OPTIONS)[default_cloud]
            self._pane.query_one(f"#{cloud_id}", RadioButton).value = True

    def build_setup_summary(self) -> str:
        preset = self.selected_preset()
        advanced = "on" if self.selected_advanced() else "off"
        summary = f" | Preset: {preset}"
        if preset == "cloud_managed":
            summary += f" ({self.selected_cloud()})"
        summary += f" | Advanced: {advanced}"
        return summary

    def update_summary_preview(self) -> None:
        preset = self.selected_preset()
        summary = f"Preset: {preset}"
        if preset == "cloud_managed":
            summary += f" ({self.selected_cloud()})"
        summary += f" | Advanced: {'on' if self.selected_advanced() else 'off'}"
        self._pane.query_one("#wizard-summary", Static).update(summary)

    def _default_preset(self) -> str:
        return "local_docker" if self._config.profile == "demo" else "cloud_managed"

    def _default_cloud(self) -> str:
        return "aws"

    def _default_advanced(self) -> bool:
        return self._config.profile in {"staging", "production"}

    def _split_tokens(self, input_id: str) -> list[str]:
        raw = self._pane.query_one(f"#{input_id}", Input).value.strip()
        if not raw:
            return []
        return [part.strip() for part in raw.replace(";", ",").split(",") if part.strip()]

    def _radio_selection(self, set_id: str, mapping: dict[str, str], default: str) -> str:
        radio = self._pane.query_one(f"#{set_id}", RadioSet)
        selected = radio.pressed_button
        if selected is None or selected.id is None:
            return default
        return mapping.get(selected.id, default)

    @staticmethod
    def _reverse_map(options: dict[str, str]) -> dict[str, str]:
        return {value: key for key, value in options.items()}


__all__ = ["WizardControls"]
