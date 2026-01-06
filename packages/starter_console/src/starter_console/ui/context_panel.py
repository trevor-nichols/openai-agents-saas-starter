from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
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


class ContextState:
    def __init__(self, ctx: CLIContext) -> None:
        self.ctx = ctx
        self._default_env_files = list(DEFAULT_ENV_FILES)
        seen = set(DEFAULT_ENV_FILES)
        custom: list[Path] = []
        for path in ctx.env_files:
            if path in seen:
                continue
            custom.append(path)
            seen.add(path)
        self._custom_env_files = custom
        self._sync_env_files()

    @property
    def default_env_files(self) -> list[Path]:
        return list(self._default_env_files)

    @property
    def custom_env_files(self) -> list[Path]:
        return list(self._custom_env_files)

    def add_custom(self, raw: str) -> tuple[bool, str]:
        value = raw.strip()
        if not value:
            return False, "Provide a path to add."
        path = Path(value).expanduser().resolve()
        if path in self._default_env_files:
            return False, "Defaults are managed by Skip env load; add custom env files only."
        if path in self._custom_env_files:
            return False, "Env file already listed."
        self._custom_env_files.append(path)
        self._sync_env_files()
        return True, f"Added {path}."

    def remove_custom(self, index: int) -> tuple[bool, str, Path | None]:
        if index < 0 or index >= len(self._custom_env_files):
            return False, "Select a custom env file row to remove.", None
        removed = self._custom_env_files.pop(index)
        self._sync_env_files()
        return True, f"Removed {removed}.", removed

    def reload_env(self, *, skip_env: bool, quiet_env: bool) -> tuple[str, EnvReloadedPayload]:
        self.ctx.skip_env = skip_env
        self.ctx.quiet_env = quiet_env
        self._sync_env_files()
        self.ctx.load_environment(verbose=not quiet_env)
        self.ctx.reset_settings_cache()
        loaded_count = len(self.ctx.loaded_env_files)
        if skip_env:
            if loaded_count:
                status = f"Defaults skipped; loaded {loaded_count} custom env file(s)."
            else:
                status = "Defaults skipped; no custom env files loaded."
        else:
            status = "Env files loaded."
        payload = EnvReloadedPayload(
            env_files=tuple(self._default_env_files + self._custom_env_files),
            skip_env=skip_env,
            quiet_env=quiet_env,
            loaded_files=tuple(self.ctx.loaded_env_files),
        )
        return status, payload

    def summary(self) -> str:
        profile, source = self._resolve_profile()
        source_label = f" ({source})" if source else ""
        default_count = len(self._default_env_files)
        custom_count = len(self._custom_env_files)
        loaded = len(self.ctx.loaded_env_files)
        total = default_count + custom_count
        return (
            f"Env: {profile}{source_label} | files: {total} (loaded {loaded}) | "
            f"skip defaults: {'yes' if self.ctx.skip_env else 'no'} | "
            f"quiet: {'yes' if self.ctx.quiet_env else 'no'}"
        )

    def _sync_env_files(self) -> None:
        self.ctx.env_files = tuple(self._default_env_files + self._custom_env_files)

    def _resolve_profile(self) -> tuple[str, str]:
        settings = self.ctx.optional_settings()
        if settings is not None:
            value = getattr(settings, "environment", None)
            if value:
                return str(value), "settings"
        env_value = os.getenv("ENVIRONMENT")
        if env_value:
            return env_value, "env"
        return "development", "default"


class ContextManageScreen(ModalScreen[None]):
    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        Binding("escape", "close", "Close", show=False),
    ]

    DEFAULT_CSS: ClassVar[str] = """
    ContextManageScreen {
        align: center middle;
    }

    #context-manage-panel {
        width: 90%;
        max-width: 110;
        background: $panel;
        border: tall $panel-darken-1;
        padding: 1 2;
    }

    #context-manage-actions {
        height: auto;
        padding-bottom: 1;
    }

    #context-manage-summary {
        color: $text-muted;
        padding-bottom: 1;
    }

    #context-manage-panel DataTable {
        height: 6;
        background: $surface;
        color: $text;
    }

    #context-manage-status {
        color: $text-muted;
        padding-top: 1;
    }
    """

    def __init__(
        self,
        state: ContextState,
        *,
        on_update: Callable[[], None],
    ) -> None:
        self._state = state
        self._on_change = on_update
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="context-manage-panel"):
            yield Static("Context", classes="context-title")
            yield Static("", id="context-manage-summary", classes="context-summary")
            with Horizontal(id="context-manage-actions"):
                yield Input(placeholder="Add custom env file path", id="context-env-input")
                yield Button("Add", id="context-env-add", variant="primary")
                yield Button("Remove", id="context-env-remove")
            with Horizontal(id="context-manage-actions"):
                yield Static("Skip default env files", classes="context-label")
                yield Switch(value=False, id="context-skip-env")
                yield Static("Quiet env load logs", classes="context-label")
                yield Switch(value=False, id="context-quiet-env")
                yield Button("Reload Env", id="context-reload", variant="primary")
                yield Button("Close", id="context-close")
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
            yield Static("", id="context-manage-status", classes="section-footnote")

    def on_mount(self) -> None:
        self.query_one("#context-skip-env", Switch).value = self._state.ctx.skip_env
        self.query_one("#context-quiet-env", Switch).value = self._state.ctx.quiet_env
        self._render_table()
        self._update_summary()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "context-env-add":
                self._add_env_file()
            case "context-env-remove":
                self._remove_selected()
            case "context-reload":
                self._reload_env()
            case "context-close":
                self.dismiss()

    def action_close(self) -> None:
        self.dismiss()

    def _add_env_file(self) -> None:
        input_field = self.query_one("#context-env-input", Input)
        ok, status = self._state.add_custom(input_field.value)
        if ok:
            input_field.value = ""
        self._render_table()
        self._update_summary()
        self._set_status(status)
        self._on_change()

    def _remove_selected(self) -> None:
        table = self.query_one("#context-custom-table", DataTable)
        if table.cursor_row is None:
            self._set_status("Select a custom env file row to remove.")
            return
        ok, status, _removed = self._state.remove_custom(table.cursor_row)
        if not ok:
            self._set_status(status)
            return
        self._render_table()
        self._update_summary()
        self._set_status(status)
        self._on_change()

    def _reload_env(self) -> None:
        skip_env = self.query_one("#context-skip-env", Switch).value
        quiet_env = self.query_one("#context-quiet-env", Switch).value
        status, payload = self._state.reload_env(skip_env=skip_env, quiet_env=quiet_env)
        self._render_table()
        self._update_summary()
        self._set_status(status)
        self._on_change()
        self.post_message(EnvReloaded(payload))

    def _render_table(self) -> None:
        defaults_table = self.query_one("#context-defaults-table", DataTable)
        defaults_table.clear(columns=True)
        defaults_table.add_columns("Env File", "Loaded", "Exists")
        loaded = set(self._state.ctx.loaded_env_files)
        for path in self._state.default_env_files:
            is_loaded = "yes" if path in loaded else "no"
            exists = "yes" if path.exists() else "no"
            defaults_table.add_row(str(path), is_loaded, exists)
        if defaults_table.row_count:
            defaults_table.focus()
            defaults_table.move_cursor(row=0, column=0)

        custom_table = self.query_one("#context-custom-table", DataTable)
        custom_table.clear(columns=True)
        custom_table.add_columns("Env File", "Loaded", "Exists")
        for path in self._state.custom_env_files:
            is_loaded = "yes" if path in loaded else "no"
            exists = "yes" if path.exists() else "no"
            custom_table.add_row(str(path), is_loaded, exists)
        if custom_table.row_count:
            custom_table.focus()
            custom_table.move_cursor(row=0, column=0)

    def _update_summary(self) -> None:
        self.query_one("#context-manage-summary", Static).update(self._state.summary())

    def _set_status(self, message: str) -> None:
        self.query_one("#context-manage-status", Static).update(message)


class ContextPanel(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="context-panel", classes="context-panel")
        self._state = ContextState(ctx)

    def compose(self) -> ComposeResult:
        with Vertical(classes="context-bar"):
            with Horizontal(classes="context-row"):
                yield Static("Context", classes="context-title")
                yield Button("Manage", id="context-manage", variant="primary")
            yield Static("", id="context-summary", classes="context-summary")

    def on_mount(self) -> None:
        self._update_summary()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "context-manage":
            self._open_manage()

    def _update_summary(self) -> None:
        self.query_one("#context-summary", Static).update(self._state.summary())

    def _open_manage(self) -> None:
        self.app.push_screen(
            ContextManageScreen(self._state, on_update=self._update_summary)
        )

__all__ = [
    "ContextManageScreen",
    "ContextPanel",
    "EnvReloaded",
    "EnvReloadedPayload",
]
