from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, Protocol, runtime_checkable

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Input, OptionList, RadioButton, RadioSet, Static

from starter_console.core import CLIContext
from starter_console.core.profiles import load_profile_registry, select_profile
from starter_console.ui.action_runner import ActionResult, ActionRunner
from starter_console.ui.panes.wizard.controls import build_profile_options
from starter_console.ui.panes.wizard.models import WizardLaunchConfig
from starter_console.ui.panes.wizard.paths import ensure_summary_paths
from starter_console.workflows.setup.editor.actions import apply_and_save
from starter_console.workflows.setup.editor.models import FieldSpec, SectionModel
from starter_console.workflows.setup.editor.sources import (
    collect_sections,
    load_setting_descriptions,
)
from starter_console.workflows.setup.editor.utils import automation_ready, missing_required

from .layout import compose_wizard_editor_layout
from .renderer import render_detail, render_fields, render_sections


class WizardEditorPane(Vertical):
    def __init__(
        self,
        ctx: CLIContext,
        *,
        config: WizardLaunchConfig | None = None,
    ) -> None:
        super().__init__(id="wizard-editor", classes="section-pane")
        self._ctx = ctx
        self._config = config or WizardLaunchConfig()
        self._profile_registry = load_profile_registry(
            project_root=ctx.project_root,
            override_path=self._config.profiles_path,
        )
        self._auto_selection = select_profile(self._profile_registry, explicit=None)
        self._profile_options = build_profile_options(self._profile_registry)
        self._profile_by_widget = {
            option.widget_id: option.profile_id for option in self._profile_options
        }
        self._widget_by_profile = {
            option.profile_id: option.widget_id for option in self._profile_options
        }
        self._invalid_profile: str | None = None
        self._answers: dict[str, str] = {
            key.strip().upper(): value
            for key, value in (self._config.answers or {}).items()
        }
        self._descriptions = load_setting_descriptions(ctx.project_root)
        self._sections: list[SectionModel] = []
        self._selected_section = 0
        self._selected_field = 0
        self._field_filter: str | None = None
        self._dirty = False
        self._active_field: FieldSpec | None = None
        self._prompt_choice_values: tuple[str, ...] = ()
        self._status_message: str | None = None
        self._action_runner: ActionRunner[None] = ActionRunner(
            ctx=self._ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_complete=self._handle_save_complete,
            on_state_change=self._set_save_state,
        )
        self._tasks: set[asyncio.Task[object]] = set()

    def compose(self) -> ComposeResult:
        yield from compose_wizard_editor_layout(self._profile_options)

    async def on_mount(self) -> None:
        self._configure_profile()
        self._set_prompt_visibility(False)
        self.set_interval(0.4, self._action_runner.refresh_output)
        await self._refresh_sections(reset_selection=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "wizard-editor-back":
            self._navigate("wizard")
        elif event.button.id == "wizard-editor-save":
            self._start_save(run_automation=False)
        elif event.button.id == "wizard-editor-save-automation":
            self._start_save(run_automation=True)
        elif event.button.id == "wizard-editor-apply":
            await self._apply_prompt()
        elif event.button.id == "wizard-editor-cancel":
            self._close_prompt()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "wizard-editor-input":
            await self._apply_prompt()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "wizard-editor-filter":
            return
        raw = event.value.strip()
        self._field_filter = raw if raw else None
        self._selected_field = 0
        self._close_prompt()
        self._clear_status_override()
        self._refresh_view()

    async def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id != "wizard-editor-profile-options":
            return
        self._selected_section = 0
        self._selected_field = 0
        self._close_prompt()
        self._clear_status_override()
        await self._refresh_sections(reset_selection=True)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "wizard-editor-sections":
            max_index = max(0, len(self._sections) - 1)
            self._selected_section = max(0, min(event.option_index, max_index))
            self._selected_field = 0
            self._close_prompt()
            self._clear_status_override()
            self._refresh_view()
            return
        if event.option_list.id == "wizard-editor-fields":
            max_index = max(0, len(self._current_fields()) - 1)
            self._selected_field = max(0, min(event.option_index, max_index))
            field = self._selected_field_spec()
            if field:
                render_detail(self, field)
                self._open_prompt(field)
            return
        if event.option_list.id == "wizard-editor-options":
            if self._active_field is None:
                return
            self._spawn_task(self._apply_prompt_choice(event.option_index))

    # ------------------------------------------------------------------
    # Rendering + state helpers
    # ------------------------------------------------------------------
    async def _refresh_sections(
        self,
        *,
        focus_key: str | None = None,
        reset_selection: bool,
    ) -> None:
        self._set_status("Loading sections...")
        profile_id = self._selected_profile()
        try:
            self._load_sections(profile_id)
        except Exception as exc:
            self._set_status(f"Failed to load sections: {exc}")
            return
        if reset_selection:
            self._selected_section = 0
            self._selected_field = 0
        self._apply_focus(focus_key)
        self._refresh_view()
        if self._status_message == "Loading sections...":
            self._status_message = None
            self._update_status()

    def _load_sections(self, profile_id: str) -> None:
        sections, _ = collect_sections(
            self._ctx,
            profile_id=profile_id,
            profiles_path=self._config.profiles_path,
            answers=self._answers,
            descriptions=self._descriptions,
            dry_run=True,
        )
        self._sections = sections

    def _apply_focus(self, focus_key: str | None) -> None:
        if not self._sections:
            self._selected_section = 0
            self._selected_field = 0
            return
        if focus_key:
            for s_idx, section in enumerate(self._sections):
                for field in section.fields:
                    if field.key == focus_key:
                        self._selected_section = s_idx
                        filtered = self._apply_filter(section.fields)
                        if not filtered:
                            self._selected_field = 0
                            return
                        for f_idx, filtered_field in enumerate(filtered):
                            if filtered_field.key == focus_key:
                                self._selected_field = f_idx
                                return
                        self._selected_field = 0
                        return
        self._selected_section = min(self._selected_section, len(self._sections) - 1)
        fields = self._current_fields()
        if fields:
            self._selected_field = min(self._selected_field, len(fields) - 1)
        else:
            self._selected_field = 0

    def _refresh_view(self) -> None:
        render_sections(
            self,
            sections=self._sections,
            selected_index=self._selected_section,
        )
        fields = self._current_fields()
        render_fields(
            self,
            fields=fields,
            selected_index=self._selected_field,
        )
        render_detail(self, self._selected_field_spec())
        self._update_summary()
        self._update_status()

    def _update_summary(self) -> None:
        profile_id = self._selected_profile()
        section = self._current_section()
        total_required = sum(
            1
            for section_item in self._sections
            for field in section_item.fields
            if field.required
        )
        missing = missing_required(self._sections)
        completed = max(0, total_required - len(missing))
        summary = f"Profile: {profile_id} | Required: {completed}/{total_required}"
        if section:
            summary += f" | Section: {section.label}"
        if self._field_filter:
            summary += f" | Filter: {self._field_filter}"
        if self._dirty:
            summary += " • Unsaved changes"
        self.query_one("#wizard-editor-summary", Static).update(summary)

    def _update_status(self) -> None:
        if self._status_message:
            self.query_one("#wizard-editor-status", Static).update(self._status_message)
            return
        if not self._sections:
            self.query_one("#wizard-editor-status", Static).update("No sections available.")
            return
        ready = automation_ready(self._sections)
        missing = missing_required(self._sections)
        status = f"Automation ready: {'yes' if ready else 'no'}"
        if missing:
            status += f" ({len(missing)} required fields missing)"
        if self._dirty:
            status = f"Unsaved changes • {status}"
        self.query_one("#wizard-editor-status", Static).update(status)

    # ------------------------------------------------------------------
    # Selection helpers
    # ------------------------------------------------------------------
    def _current_section(self) -> SectionModel | None:
        if not self._sections:
            return None
        if self._selected_section < 0 or self._selected_section >= len(self._sections):
            return None
        return self._sections[self._selected_section]

    def _current_fields(self) -> list[FieldSpec]:
        section = self._current_section()
        if not section:
            return []
        return self._apply_filter(section.fields)

    def _selected_field_spec(self) -> FieldSpec | None:
        fields = self._current_fields()
        if not fields:
            return None
        if self._selected_field < 0 or self._selected_field >= len(fields):
            return None
        return fields[self._selected_field]

    def _apply_filter(self, fields: list[FieldSpec]) -> list[FieldSpec]:
        if not self._field_filter:
            return fields
        needle = self._field_filter.lower()
        return [
            field
            for field in fields
            if needle in field.key.lower() or needle in field.label.lower()
        ]

    # ------------------------------------------------------------------
    # Prompt handling
    # ------------------------------------------------------------------
    def _open_prompt(self, field: FieldSpec) -> None:
        self._active_field = field
        label = f"{field.label} [{field.key}]"
        detail_parts = ["Required" if field.required else "Optional"]
        if field.default:
            detail_parts.append(f"Default: {field.default}")
        if field.kind == "secret":
            detail_parts.append("Leave blank to clear.")
        detail = " | ".join(detail_parts)
        self.query_one("#wizard-editor-prompt-label", Static).update(label)
        self.query_one("#wizard-editor-prompt-detail", Static).update(detail)
        self._set_prompt_status("")
        input_field = self.query_one("#wizard-editor-input", Input)
        option_list = self.query_one("#wizard-editor-options", OptionList)
        if field.kind in {"string", "secret"}:
            input_field.password = field.kind == "secret"
            if field.kind == "secret":
                input_field.value = ""
            else:
                input_field.value = field.value or field.default or ""
            option_list.clear_options()
            self._prompt_choice_values = ()
            self._set_prompt_visibility(True, show_input=True)
            input_field.focus()
            return
        option_list.clear_options()
        labels, values = self._build_choice_options(field)
        for label_text in labels:
            option_list.add_option(label_text)
        self._prompt_choice_values = tuple(values)
        highlighted = self._choice_highlight_index(field, values)
        if highlighted is not None:
            option_list.highlighted = highlighted
        input_field.value = ""
        self._set_prompt_visibility(True, show_input=False)
        option_list.focus()

    async def _apply_prompt(self) -> None:
        field = self._active_field
        if field is None:
            self._set_prompt_status("Choose a field first.")
            return
        value = self._resolve_prompt_value(field)
        if value is None:
            return
        previous = self._answers.get(field.key)
        self._answers[field.key] = value
        if value != previous:
            self._dirty = True
        self._close_prompt()
        await self._refresh_sections(focus_key=field.key, reset_selection=False)

    async def _apply_prompt_choice(self, index: int) -> None:
        if index < 0 or index >= len(self._prompt_choice_values):
            self._set_prompt_status("Choose an option.")
            return
        option_list = self.query_one("#wizard-editor-options", OptionList)
        option_list.highlighted = index
        await self._apply_prompt()

    def _resolve_prompt_value(self, field: FieldSpec) -> str | None:
        if field.kind in {"string", "secret"}:
            raw = self.query_one("#wizard-editor-input", Input).value
            return raw.strip()
        option_list = self.query_one("#wizard-editor-options", OptionList)
        index = option_list.highlighted
        if index is None or index < 0 or index >= len(self._prompt_choice_values):
            self._set_prompt_status("Choose an option.")
            return None
        value = self._prompt_choice_values[index]
        if field.kind == "bool":
            return "true" if value == "true" else "false"
        return value

    def _build_choice_options(self, field: FieldSpec) -> tuple[list[str], list[str]]:
        if field.kind == "bool":
            return ["Yes", "No"], ["true", "false"]
        labels: list[str] = []
        values: list[str] = []
        for choice in field.choices:
            detail = field.choice_help.get(choice)
            if detail:
                labels.append(f"{choice} — {detail}")
            else:
                labels.append(choice)
            values.append(choice)
        return labels, values

    def _choice_highlight_index(self, field: FieldSpec, values: list[str]) -> int | None:
        if field.kind == "bool":
            current = (field.value or field.default or "").strip().lower()
            if current in {"1", "true", "yes", "y"}:
                return 0
            if current in {"0", "false", "no", "n"}:
                return 1
            return 0
        current = (field.value or field.default or "").strip()
        if not current:
            return 0 if values else None
        if current in values:
            return values.index(current)
        return 0 if values else None

    def _close_prompt(self) -> None:
        self._active_field = None
        self._prompt_choice_values = ()
        self._set_prompt_visibility(False)
        self._set_prompt_status("")

    def _set_prompt_visibility(self, visible: bool, *, show_input: bool = True) -> None:
        prompt = self.query_one("#wizard-editor-prompt", Vertical)
        input_field = self.query_one("#wizard-editor-input", Input)
        option_list = self.query_one("#wizard-editor-options", OptionList)
        prompt.display = visible
        input_field.display = visible and show_input
        option_list.display = visible and not show_input
        self.query_one("#wizard-editor-prompt-actions").display = visible
        self.query_one("#wizard-editor-prompt-label", Static).display = visible
        self.query_one("#wizard-editor-prompt-detail", Static).display = visible
        self.query_one("#wizard-editor-prompt-status", Static).display = visible

    def _set_prompt_status(self, message: str) -> None:
        self.query_one("#wizard-editor-prompt-status", Static).update(message)

    # ------------------------------------------------------------------
    # Save handling
    # ------------------------------------------------------------------
    def _start_save(self, *, run_automation: bool) -> None:
        if self._action_runner.running:
            self._set_status("Save already running.")
            return
        if run_automation and not automation_ready(self._sections):
            self._set_status("Automation disabled: missing required values.")
            return
        profile_id = self._selected_profile()
        summary_path, markdown_path = ensure_summary_paths(
            self._ctx,
            self._config.summary_path,
            self._config.markdown_summary_path,
        )
        answers = dict(self._answers)
        label = "Wizard Editor Save"
        if run_automation:
            label = "Wizard Editor Save + Automation"

        def _runner(ctx: CLIContext) -> None:
            apply_and_save(
                ctx,
                profile_id=profile_id,
                profiles_path=self._config.profiles_path,
                answers=answers,
                summary_path=summary_path,
                markdown_summary_path=markdown_path,
                export_answers_path=self._config.export_answers_path,
                output_format=self._config.output_format,
                run_automation=run_automation,
            )

        if not self._action_runner.start(label, _runner):
            self._set_status("Save already running.")

    def _set_save_state(self, running: bool) -> None:
        self.query_one("#wizard-editor-save", Button).disabled = running
        self.query_one("#wizard-editor-save-automation", Button).disabled = running

    def _handle_save_complete(self, result: ActionResult[None]) -> None:
        if result.error is None:
            self._dirty = False
            self._spawn_task(self._refresh_sections(reset_selection=False))

    def _set_output(self, message: str) -> None:
        self.query_one("#wizard-editor-output", Static).update(message)

    # ------------------------------------------------------------------
    # Profile helpers
    # ------------------------------------------------------------------
    def _configure_profile(self) -> None:
        profile_id = self._resolve_profile_id()
        widget_id = self._widget_by_profile.get(profile_id)
        if widget_id:
            self.query_one(f"#{widget_id}", RadioButton).value = True
        if self._invalid_profile:
            self._set_status(
                f"Profile '{self._invalid_profile}' not found. Using '{profile_id}' instead."
            )

    def _resolve_profile_id(self) -> str:
        profile_id = self._config.profile or None
        if profile_id:
            profile_id = profile_id.strip().lower()
        if profile_id and profile_id in self._profile_registry.profiles:
            self._invalid_profile = None
            return profile_id
        if profile_id:
            self._invalid_profile = profile_id
        return self._auto_selection.profile.profile_id

    def _selected_profile(self) -> str:
        radio = self.query_one("#wizard-editor-profile-options", RadioSet)
        selected = radio.pressed_button
        if not selected or not selected.id:
            return self._resolve_profile_id()
        return self._profile_by_widget.get(selected.id, self._resolve_profile_id())

    # ------------------------------------------------------------------
    # Navigation + status
    # ------------------------------------------------------------------
    def _navigate(self, route: str) -> None:
        app = self.app
        if isinstance(app, _Navigator):
            app.action_go(route)

    def _set_status(self, message: str) -> None:
        self._status_message = message
        self.query_one("#wizard-editor-status", Static).update(message)

    def _clear_status_override(self) -> None:
        if self._status_message:
            self._status_message = None

    def _spawn_task(self, coro: Coroutine[Any, Any, object]) -> None:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)


__all__ = ["WizardEditorPane"]


@runtime_checkable
class _Navigator(Protocol):
    def action_go(self, section_key: str) -> None: ...
