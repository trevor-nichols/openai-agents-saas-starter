from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from textual.app import ComposeResult
from textual.widgets import Button, Collapsible, DataTable, Static

from starter_console.core import CLIContext
from starter_console.core.status_models import ProbeResult, ServiceStatus
from starter_console.workflows.home.hub import HubService

from ..view_models import format_summary, probe_rows, service_rows
from .footer_pane import FooterPane


class HomePane(FooterPane):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(pane_id="home")
        self.ctx = ctx
        self.hub = hub
        self._summary: dict[str, int] = {}
        self._probes: list[ProbeResult] = []
        self._services: list[ServiceStatus] = []
        self._profile: str = "local"
        self._strict: bool = False
        self._stack_state: str | None = None

    def compose_body(self) -> ComposeResult:
        yield Static("Home", classes="section-title")
        yield Static(
            "Operational overview for this workspace.",
            classes="section-description",
        )
        yield Static("", id="home-summary", classes="section-summary home-summary-card")
        with Collapsible(title="Probe health", id="home-probes-card", collapsed=False):
            yield DataTable(id="home-probes", zebra_stripes=True)
        with Collapsible(title="Service status", id="home-services-card", collapsed=False):
            yield DataTable(id="home-services", zebra_stripes=True)

    def compose_footer(self) -> ComposeResult:
        yield Button("Refresh", id="home-refresh", variant="primary")
        yield self.footer_spacer()
        yield Static("", id="home-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "home-refresh":
            await self.refresh_data()

    async def refresh_data(self) -> None:
        self._set_status("Refreshing status...")
        await asyncio.to_thread(self._collect)
        self._render_summary()
        self._render_tables()
        self._set_status(self._timestamp_label())

    def _collect(self) -> None:
        snapshot = self.hub.load_home()
        self._probes = list(snapshot.probes)
        self._services = list(snapshot.services)
        self._summary = snapshot.summary
        self._profile = snapshot.profile
        self._strict = snapshot.strict
        self._stack_state = snapshot.stack_state

    def _render_summary(self) -> None:
        summary_text = format_summary(
            self._summary,
            profile=self._profile,
            strict=self._strict,
            stack_state=self._stack_state,
        )
        self.query_one("#home-summary", Static).update(summary_text)

    def _render_tables(self) -> None:
        probe_table = self.query_one("#home-probes", DataTable)
        probe_table.clear(columns=True)
        probe_table.add_columns("Probe", "Status", "Detail")
        probe_items = probe_rows(self._probes)
        if not probe_items:
            probe_table.add_row("No probes detected", "-", "Run Doctor to populate.")
        else:
            for row in probe_items:
                probe_table.add_row(*row)

        service_table = self.query_one("#home-services", DataTable)
        service_table.clear(columns=True)
        service_table.add_columns("Service", "Status", "Detail")
        service_items = service_rows(self._services)
        if not service_items:
            service_table.add_row("No services detected", "-", "Start the stack or run Doctor.")
        else:
            for row in service_items:
                service_table.add_row(*row)

    def _set_status(self, message: str) -> None:
        self.query_one("#home-status", Static).update(message)

    def _timestamp_label(self) -> str:
        now = datetime.now(UTC).astimezone()
        return f"Updated {now.strftime('%H:%M:%S')}"


__all__ = ["HomePane"]
