from __future__ import annotations

import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from textual.widgets import Input, RadioButton, RadioSet, Static, Switch

from starter_console.adapters.env import EnvFile
from starter_console.core import CLIContext, CLIError
from starter_console.core.profiles import (
    PROFILE_ENV_KEY,
    ProfileRegistry,
    ProfileSelection,
    ProfileSource,
    locked_env_statuses,
)
from starter_console.workflows.setup.automation import ALL_AUTOMATION_PHASES, AutomationPhase
from starter_console.workflows.setup.inputs import (
    ParsedAnswers,
    load_answers_files,
    merge_answer_overrides,
)

from .models import ProfileOption, WizardLaunchConfig


class _QueryPane(Protocol):
    def query_one(self, *args: Any, **kwargs: Any) -> Any: ...


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


def build_profile_options(registry: ProfileRegistry) -> tuple[ProfileOption, ...]:
    options: list[ProfileOption] = []
    for profile_id in registry.profile_ids:
        policy = registry.profiles[profile_id]
        options.append(
            ProfileOption(
                profile_id=profile_id,
                label=policy.label or profile_id,
                description=policy.description or "",
                widget_id=_profile_widget_id(profile_id),
            )
        )
    return tuple(options)


def _profile_widget_id(profile_id: str) -> str:
    slug = re.sub(r"[^a-z0-9_-]+", "-", profile_id.strip().lower()).strip("-")
    return f"profile-{slug or 'default'}"


class WizardControls:
    def __init__(
        self,
        pane: _QueryPane,
        config: WizardLaunchConfig,
        *,
        ctx: CLIContext,
        profile_registry: ProfileRegistry,
        auto_selection: ProfileSelection,
        profile_options: tuple[ProfileOption, ...],
    ) -> None:
        self._pane = pane
        self._config = config
        self._ctx = ctx
        self._registry = profile_registry
        self._auto_selection = auto_selection
        self._profile_options = profile_options
        self._profile_by_widget = {
            option.widget_id: option.profile_id for option in profile_options
        }
        self._widget_by_profile = {
            option.profile_id: option.widget_id for option in profile_options
        }
        self._invalid_profile: str | None = None

    def configure_profile(self) -> None:
        profile_id = self._resolve_profile_id()
        self._config.profile = profile_id
        widget_id = self._widget_by_profile.get(profile_id)
        if widget_id:
            self._pane.query_one(f"#{widget_id}", RadioButton).value = True
        self.update_profile_context()
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
        fallback = self._resolve_profile_id()
        return self._radio_selection("wizard-profile", self._profile_by_widget, fallback)

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
        profile = self.selected_profile()
        preset = self.selected_preset()
        advanced = "on" if self.selected_advanced() else "off"
        summary = f" | Profile: {profile} | Preset: {preset}"
        if preset == "cloud_managed":
            summary += f" ({self.selected_cloud()})"
        summary += f" | Advanced: {advanced}"
        return summary

    def update_summary_preview(self) -> None:
        profile = self.selected_profile()
        preset = self.selected_preset()
        summary = f"Profile: {profile} | Preset: {preset}"
        if preset == "cloud_managed":
            summary += f" ({self.selected_cloud()})"
        summary += f" | Advanced: {'on' if self.selected_advanced() else 'off'}"
        self._pane.query_one("#wizard-summary", Static).update(summary)

    def update_profile_context(self) -> None:
        profile_id = self.selected_profile()
        option = self._option_for_profile(profile_id)
        selected_label = option.label if option else profile_id
        if option and option.label != profile_id:
            selected_line = f"Selected: {selected_label} [{profile_id}]"
        else:
            selected_line = f"Selected: {profile_id}"
        if option and option.description:
            selected_line += f" — {option.description}"
        if self._invalid_profile:
            selected_line = (
                f"Selected: {profile_id} (fallback; '{self._invalid_profile}' not found)"
            )
        auto = self._auto_selection
        auto_label = self._option_for_profile(auto.profile.profile_id)
        auto_name = auto_label.label if auto_label else auto.profile.profile_id
        auto_source = self._format_auto_source(auto)
        auto_line = f"Auto-select: {auto_name} [{auto.profile.profile_id}] — {auto_source}"
        hint = "\n".join(filter(None, [selected_line, auto_line]))
        self._pane.query_one("#wizard-profile-hint", Static).update(hint)

        policy = self._profile_policy(profile_id)
        locks = self._format_lock_summary(policy)
        self._pane.query_one("#wizard-profile-locks", Static).update(locks)

    def _resolve_profile_id(self) -> str:
        profile_id = self._config.profile or None
        if profile_id:
            profile_id = profile_id.strip().lower()
        if profile_id and profile_id in self._registry.profiles:
            self._invalid_profile = None
            return profile_id
        if profile_id:
            self._invalid_profile = profile_id
        return self._auto_selection.profile.profile_id

    def _profile_policy(self, profile_id: str | None = None):
        resolved = profile_id or self.selected_profile()
        return self._registry.profiles.get(resolved, self._auto_selection.profile)

    def _option_for_profile(self, profile_id: str) -> ProfileOption | None:
        for option in self._profile_options:
            if option.profile_id == profile_id:
                return option
        return None

    def _format_auto_source(self, selection: ProfileSelection) -> str:
        source = selection.source
        if source is ProfileSource.CONFIG:
            if selection.config_path:
                return f"config ({selection.config_path})"
            return "config"
        if source is ProfileSource.ENV:
            if selection.env_profile:
                return f"env ({PROFILE_ENV_KEY}={selection.env_profile})"
            return "env"
        if source is ProfileSource.DETECT:
            return "detected"
        if source is ProfileSource.DEFAULT:
            return "default"
        return source.value

    def _format_lock_summary(self, policy) -> str:
        try:
            locked = locked_env_statuses(
                policy,
                backend_env=dict(os.environ),
                frontend_env=self._load_frontend_env(),
            )
        except CLIError as exc:
            return f"Locked: error ({exc})"
        if not locked:
            return "Locked: none"
        scopes = {status.scope for status in locked}
        include_scope = len(scopes) > 1
        locked_items = ", ".join(self._lock_item(status, include_scope) for status in locked)
        overrides = [status for status in locked if status.overridden]
        if overrides:
            override_items = ", ".join(
                self._override_item(status, include_scope) for status in overrides
            )
            return f"Locked: {locked_items}\nOverrides: {override_items}"
        return f"Locked: {locked_items}"

    def _lock_item(self, status, include_scope: bool) -> str:
        prefix = f"{status.scope}." if include_scope else ""
        value = status.current or status.default
        return f"{prefix}{status.key}={value}"

    def _override_item(self, status, include_scope: bool) -> str:
        prefix = f"{status.scope}." if include_scope else ""
        actual = status.current or ""
        return f"{prefix}{status.key}={actual} (expected {status.default})"

    def _load_frontend_env(self) -> dict[str, str]:
        path = self._ctx.project_root / "apps" / "web-app" / ".env.local"
        if not path.exists():
            return {}
        return EnvFile(path).as_dict()

    def _default_preset(self) -> str:
        policy = self._profile_policy()
        return policy.wizard.hosting_preset_default or "local_docker"

    def _default_cloud(self) -> str:
        policy = self._profile_policy()
        return policy.wizard.cloud_provider_default or "aws"

    def _default_advanced(self) -> bool:
        policy = self._profile_policy()
        return bool(policy.wizard.show_advanced_default)

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


__all__ = ["WizardControls", "build_profile_options"]
