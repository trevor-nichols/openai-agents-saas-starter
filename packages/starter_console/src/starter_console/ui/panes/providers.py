from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.containers import Grid, Vertical
from textual.widgets import Button, DataTable, RadioButton, RadioSet, Static

from starter_console.core import CLIContext
from starter_console.workflows.home.hub import HubService


class ProvidersPane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="providers", classes="section-pane")
        self.ctx = ctx
        self.hub = hub

    def compose(self) -> ComposeResult:
        yield Static("Providers", classes="section-title")
        yield Static("Validate provider configuration status.", classes="section-description")
        with Grid(classes="form-grid"):
            yield Static("", classes="wizard-control-label")
            yield Button("Refresh", id="providers-refresh", variant="primary")
            yield Static("Strict mode", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Auto", id="providers-strict-auto"),
                RadioButton("Strict", id="providers-strict-on"),
                RadioButton("Relaxed", id="providers-strict-off"),
                id="providers-strict",
            )
        yield DataTable(id="providers-table", zebra_stripes=True)
        yield Static("", id="providers-status", classes="section-footnote")

    async def on_mount(self) -> None:
        self._configure_defaults()
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "providers-refresh":
            await self.refresh_data()

    async def refresh_data(self) -> None:
        self.query_one("#providers-status", Static).update("Validating providers...")
        snapshot = await asyncio.to_thread(
            self.hub.load_providers, strict_override=self._resolve_strict_override()
        )
        table = self.query_one("#providers-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Provider", "Severity", "Message")
        if snapshot.error:
            table.add_row("settings", "error", "Settings unavailable; load env files first.")
            self.query_one("#providers-status", Static).update("Unable to load settings.")
            return
        violations = snapshot.violations
        if not violations:
            table.add_row("all", "ok", "All providers are configured.")
            self.query_one("#providers-status", Static).update("Provider validation passed.")
            return
        for violation in violations:
            severity = "fatal" if violation.fatal else "warn"
            table.add_row(violation.provider, severity, violation.message)
        self.query_one("#providers-status", Static).update(
            "Provider validation finished with findings."
        )

    def _configure_defaults(self) -> None:
        self.query_one("#providers-strict-auto", RadioButton).value = True

    def _resolve_strict_override(self) -> bool | None:
        radio = self.query_one("#providers-strict", RadioSet)
        selected = radio.pressed_button
        if selected is None or selected.id is None:
            return None
        if selected.id.endswith("auto"):
            return None
        return selected.id.endswith("on")


__all__ = ["ProvidersPane"]
