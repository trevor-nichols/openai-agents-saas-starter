from __future__ import annotations

import json
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, RadioButton, RadioSet, Static

from starter_cli.core import CLIContext
from starter_cli.services.config.inventory import (
    collect_field_specs,
    format_default,
    render_markdown,
)
from starter_cli.ui.action_runner import ActionRunner


class ConfigInventoryPane(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="config-inventory", classes="section-pane")
        self.ctx = ctx
        self._runner: ActionRunner[int] = ActionRunner(
            ctx=self.ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_state_change=self._set_action_state,
        )

    def compose(self) -> ComposeResult:
        yield Static("Config Inventory", classes="section-title")
        yield Static(
            "Inspect settings schema and export inventory docs.",
            classes="section-description",
        )
        with Horizontal(classes="ops-actions"):
            yield Button("Dump Schema", id="config-dump", variant="primary")
            yield Button("Write Inventory", id="config-write")
            yield Static("Format", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Table", id="config-format-table"),
                RadioButton("JSON", id="config-format-json"),
                id="config-format",
            )
        with Horizontal(classes="ops-actions"):
            yield Static("Inventory path", classes="wizard-control-label")
            yield Input(
                id="config-inventory-path",
                value="docs/trackers/CLI_ENV_INVENTORY.md",
            )
        yield DataTable(id="config-schema", zebra_stripes=True)
        yield Static("", id="config-status", classes="section-footnote")
        yield Static("", id="config-output", classes="ops-output")

    def on_mount(self) -> None:
        self.query_one("#config-format-table", RadioButton).value = True
        self.set_interval(0.4, self._runner.refresh_output)
        self._render_table([])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "config-dump":
            self._dump_schema()
        elif event.button.id == "config-write":
            self._write_inventory()

    def _dump_schema(self) -> None:
        field_specs = collect_field_specs()
        format_choice = self._selected_format()
        if format_choice == "json":
            payload = [spec.to_dict() for spec in field_specs]
            self._set_output(json.dumps(payload, indent=2))
            self._set_status("Rendered schema JSON.")
            return
        self._render_table(field_specs)
        self._set_output("")
        self._set_status("Rendered schema table.")

    def _write_inventory(self) -> None:
        destination = self._inventory_path()

        def _runner(_: CLIContext) -> int:
            body = render_markdown(collect_field_specs())
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(body, encoding="utf-8")
            return 0

        if not self._runner.start("Write inventory", _runner):
            self._set_status("Inventory export already running.")

    def _render_table(self, field_specs) -> None:
        table = self.query_one("#config-schema", DataTable)
        table.clear(columns=True)
        table.add_columns("Env Var", "Type", "Default", "Wizard", "Required")
        if not field_specs:
            table.add_row("-", "-", "-", "-", "-")
            return
        for spec in field_specs:
            default_value = format_default(spec.default, spec.required)
            table.add_row(
                spec.env_var,
                spec.type_hint,
                default_value or "",
                "yes" if spec.wizard_prompted else "",
                "yes" if spec.required else "",
            )

    def _selected_format(self) -> str:
        radio = self.query_one("#config-format", RadioSet)
        selected = radio.pressed_button
        if selected is None or selected.id is None:
            return "table"
        return "json" if selected.id.endswith("json") else "table"

    def _inventory_path(self) -> Path:
        raw = self.query_one("#config-inventory-path", Input).value.strip()
        path = Path(raw).expanduser()
        return path if path.is_absolute() else (self.ctx.project_root / path).resolve()

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#config-write", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#config-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#config-output", Static).update(message)


__all__ = ["ConfigInventoryPane"]
