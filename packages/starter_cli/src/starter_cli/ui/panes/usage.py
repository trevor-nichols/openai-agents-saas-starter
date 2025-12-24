from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from starter_cli.core import CLIContext
from starter_cli.services.ops_models import UsageWarning
from starter_cli.workflows.home.hub import HubService


class UsagePane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="usage", classes="section-pane")
        self.ctx = ctx
        self.hub = hub

    def compose(self) -> ComposeResult:
        yield Static("Usage", classes="section-title")
        yield Static("Usage reports and entitlement artifacts.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Button("Refresh", id="usage-refresh", variant="primary")
        yield DataTable(id="usage-summary", zebra_stripes=True)
        yield DataTable(id="usage-warnings", zebra_stripes=True)
        yield Static("", id="usage-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "usage-refresh":
            await self.refresh_data()

    async def refresh_data(self) -> None:
        snapshot = await asyncio.to_thread(self.hub.load_usage)
        summary_table = self.query_one("#usage-summary", DataTable)
        summary_table.clear(columns=True)
        summary_table.add_columns("Metric", "Value")
        if snapshot.summary is None:
            summary_table.add_row("Report", "Not found")
            self.query_one("#usage-status", Static).update(
                "Run `starter-cli usage export-report` to generate artifacts."
            )
            self._render_warnings([])
            return
        summary = snapshot.summary
        summary_table.add_row("Generated at", summary.generated_at or "unknown")
        summary_table.add_row("Tenants", str(summary.tenant_count))
        summary_table.add_row("Features", str(summary.feature_count))
        summary_table.add_row("Warnings", str(summary.warning_count))
        self._render_warnings(list(snapshot.warnings))
        self.query_one("#usage-status", Static).update("Usage report loaded.")

    def _render_warnings(self, warnings: list[UsageWarning]) -> None:
        warnings_table = self.query_one("#usage-warnings", DataTable)
        warnings_table.clear(columns=True)
        warnings_table.add_columns("Tenant", "Feature", "Status")
        if not warnings:
            warnings_table.add_row("-", "-", "No warnings in report")
            return
        for warning in warnings:
            warnings_table.add_row(warning.tenant_slug, warning.feature_key, warning.status)


__all__ = ["UsagePane"]
