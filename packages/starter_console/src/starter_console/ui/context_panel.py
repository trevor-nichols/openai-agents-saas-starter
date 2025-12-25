from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, DataTable, Input, Static, Switch

from starter_console.core import CLIContext
from starter_console.core.constants import DEFAULT_ENV_FILES


@dataclass(frozen=True, slots=True)
class EnvReloadedPayload:
    env_files: tuple[Path, ...]
    skip_env: bool
    quiet_env: bool
    loaded_files: tuple[Path, ...]


class EnvReloaded(Message):
    def __init__(self, payload: EnvReloadedPayload) -> None:
        self.payload = payload
        super().__init__()


class ContextPanel(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="context-panel", classes="context-panel")
        self._ctx = ctx
        self._default_env_files = list(DEFAULT_ENV_FILES)
        seen = set(DEFAULT_ENV_FILES)
        custom: list[Path] = []
        for path in ctx.env_files:
            if path in seen:
                continue
            custom.append(path)
            seen.add(path)
        self._custom_env_files = custom

    def compose(self) -> ComposeResult:
        yield Static("Context", classes="context-title")
        yield Static("", id="context-summary", classes="context-summary")
        with Horizontal(classes="context-actions"):
            yield Input(placeholder="Add custom env file path", id="context-env-input")
            yield Button("Add", id="context-env-add", variant="primary")
            yield Button("Remove", id="context-env-remove")
        with Horizontal(classes="context-actions"):
            yield Static("Skip default env files", classes="context-label")
            yield Switch(value=False, id="context-skip-env")
            yield Static("Quiet env load logs", classes="context-label")
            yield Switch(value=False, id="context-quiet-env")
            yield Button("Reload Env", id="context-reload", variant="primary")
        yield Static(
            "Default env files (repo-managed; use Skip default env files to ignore)",
            classes="context-label",
        )
        yield DataTable(id="context-defaults-table", zebra_stripes=True)
        yield Static(
            "Custom env files (added here; can be removed anytime)",
            classes="context-label",
        )
        yield DataTable(id="context-custom-table", zebra_stripes=True)
        yield Static("", id="context-status", classes="section-footnote")

    def on_mount(self) -> None:
        self._ctx.env_files = tuple(self._default_env_files + self._custom_env_files)
        self.query_one("#context-skip-env", Switch).value = self._ctx.skip_env
        self.query_one("#context-quiet-env", Switch).value = self._ctx.quiet_env
        self._render_table()
        self._update_summary()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "context-env-add":
            self._add_env_file()
        elif event.button.id == "context-env-remove":
            self._remove_selected()
        elif event.button.id == "context-reload":
            self._reload_env()

    def _add_env_file(self) -> None:
        input_field = self.query_one("#context-env-input", Input)
        raw = input_field.value.strip()
        if not raw:
            self._set_status("Provide a path to add.")
            return
        path = Path(raw).expanduser().resolve()
        if path in self._default_env_files:
            self._set_status("Defaults are managed by Skip env load; add custom env files only.")
            return
        if path in self._custom_env_files:
            self._set_status("Env file already listed.")
            return
        self._custom_env_files.append(path)
        input_field.value = ""
        self._render_table()
        self._update_summary()
        self._set_status(f"Added {path}.")

    def _remove_selected(self) -> None:
        table = self.query_one("#context-custom-table", DataTable)
        if table.cursor_row is None:
            self._set_status("Select a custom env file row to remove.")
            return
        if table.cursor_row < 0 or table.cursor_row >= len(self._custom_env_files):
            self._set_status("Selection out of range.")
            return
        removed = self._custom_env_files.pop(table.cursor_row)
        self._render_table()
        self._update_summary()
        self._set_status(f"Removed {removed}.")

    def _reload_env(self) -> None:
        skip_env = self.query_one("#context-skip-env", Switch).value
        quiet_env = self.query_one("#context-quiet-env", Switch).value
        self._ctx.env_files = tuple(self._default_env_files + self._custom_env_files)
        self._ctx.skip_env = skip_env
        self._ctx.quiet_env = quiet_env
        self._ctx.load_environment(verbose=not quiet_env)
        self._ctx.reset_settings_cache()
        self._render_table()
        self._update_summary()
        loaded_count = len(self._ctx.loaded_env_files)
        if skip_env:
            if loaded_count:
                status = f"Defaults skipped; loaded {loaded_count} custom env file(s)."
            else:
                status = "Defaults skipped; no custom env files loaded."
        else:
            status = "Env files loaded."
        self._set_status(status)
        self.post_message(
            EnvReloaded(
                EnvReloadedPayload(
                    env_files=tuple(self._default_env_files + self._custom_env_files),
                    skip_env=skip_env,
                    quiet_env=quiet_env,
                    loaded_files=tuple(self._ctx.loaded_env_files),
                )
            )
        )

    def _render_table(self) -> None:
        defaults_table = self.query_one("#context-defaults-table", DataTable)
        defaults_table.clear(columns=True)
        defaults_table.add_columns("Env File", "Loaded", "Exists")
        loaded = set(self._ctx.loaded_env_files)
        for path in self._default_env_files:
            is_loaded = "yes" if path in loaded else "no"
            exists = "yes" if path.exists() else "no"
            defaults_table.add_row(str(path), is_loaded, exists)
        if defaults_table.row_count:
            defaults_table.focus()
            defaults_table.move_cursor(row=0, column=0)

        custom_table = self.query_one("#context-custom-table", DataTable)
        custom_table.clear(columns=True)
        custom_table.add_columns("Env File", "Loaded", "Exists")
        for path in self._custom_env_files:
            is_loaded = "yes" if path in loaded else "no"
            exists = "yes" if path.exists() else "no"
            custom_table.add_row(str(path), is_loaded, exists)
        if custom_table.row_count:
            custom_table.focus()
            custom_table.move_cursor(row=0, column=0)

    def _update_summary(self) -> None:
        profile, source = self._resolve_profile()
        source_label = f" ({source})" if source else ""
        summary = f"Profile: {profile}{source_label}"
        default_count = len(self._default_env_files)
        custom_count = len(self._custom_env_files)
        summary += f" | env files: {default_count + custom_count}"
        summary += f" (defaults {default_count}, custom {custom_count})"
        loaded = len(self._ctx.loaded_env_files)
        summary += f" | loaded: {loaded}"
        summary += f" | skip defaults: {'yes' if self._ctx.skip_env else 'no'}"
        summary += f" | quiet: {'yes' if self._ctx.quiet_env else 'no'}"
        self.query_one("#context-summary", Static).update(summary)

    def _resolve_profile(self) -> tuple[str, str]:
        settings = self._ctx.optional_settings()
        if settings is not None:
            value = getattr(settings, "environment", None)
            if value:
                return str(value), "settings"
        env_value = os.getenv("ENVIRONMENT")
        if env_value:
            return env_value, "env"
        return "development", "default"

    def _set_status(self, message: str) -> None:
        self.query_one("#context-status", Static).update(message)


__all__ = ["ContextPanel", "EnvReloaded", "EnvReloadedPayload"]
