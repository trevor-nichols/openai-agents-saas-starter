from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Static, Switch

from starter_console.core import CLIContext

from ..context_state import ContextState, EnvReloaded


class ContextPane(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="context", classes="section-pane")
        self.ctx = ctx
        self._state = ContextState(ctx)

    def compose(self) -> ComposeResult:
        yield Static("Context", classes="section-title")
        yield Static(
            "Manage env files, profiles, and runtime context settings.",
            classes="section-description",
        )
        yield Static("", id="context-summary", classes="section-summary")
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
            "Default env files (repo-managed; use Skip default env files to ignore).",
            classes="context-label",
        )
        yield DataTable(id="context-defaults-table", zebra_stripes=True, classes="context-table")
        yield Static(
            "Custom env files (added here; can be removed anytime).",
            classes="context-label",
        )
        yield DataTable(id="context-custom-table", zebra_stripes=True, classes="context-table")
        yield Static("", id="context-status", classes="section-footnote")

    def on_mount(self) -> None:
        self.query_one("#context-skip-env", Switch).value = self._state.ctx.skip_env
        self.query_one("#context-quiet-env", Switch).value = self._state.ctx.quiet_env
        self.refresh_data()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "context-env-add":
                self._add_env_file()
            case "context-env-remove":
                self._remove_selected()
            case "context-reload":
                self._reload_env()

    def refresh_data(self) -> None:
        self._render_table()
        self._update_summary()

    def _add_env_file(self) -> None:
        input_field = self.query_one("#context-env-input", Input)
        ok, status = self._state.add_custom(input_field.value)
        if ok:
            input_field.value = ""
        self.refresh_data()
        self._set_status(status)

    def _remove_selected(self) -> None:
        table = self.query_one("#context-custom-table", DataTable)
        if table.cursor_row is None:
            self._set_status("Select a custom env file row to remove.")
            return
        ok, status, _removed = self._state.remove_custom(table.cursor_row)
        if not ok:
            self._set_status(status)
            return
        self.refresh_data()
        self._set_status(status)

    def _reload_env(self) -> None:
        skip_env = self.query_one("#context-skip-env", Switch).value
        quiet_env = self.query_one("#context-quiet-env", Switch).value
        status, payload = self._state.reload_env(skip_env=skip_env, quiet_env=quiet_env)
        self._set_status(status)
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
        self.query_one("#context-summary", Static).update(self._state.summary())

    def _set_status(self, message: str) -> None:
        self.query_one("#context-status", Static).update(message)


__all__ = ["ContextPane"]
