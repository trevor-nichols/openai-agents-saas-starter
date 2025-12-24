from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from starter_cli.core import CLIContext
from starter_cli.services.ops_models import mask_value
from starter_cli.services.stripe_status import REQUIRED_ENV_KEYS, StripeStatus
from starter_cli.workflows.home.hub import HubService


class StripePane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="stripe", classes="section-pane")
        self.ctx = ctx
        self.hub = hub
        self._env_values: dict[str, str | None] = {}

    def compose(self) -> ComposeResult:
        yield Static("Stripe", classes="section-title")
        yield Static("Stripe billing configuration overview.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Button("Refresh", id="stripe-refresh", variant="primary")
            yield Button("Show Setup Command", id="stripe-setup")
            yield Button("Show Webhook Command", id="stripe-webhook")
        yield DataTable(id="stripe-table", zebra_stripes=True)
        yield Static("", id="stripe-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "stripe-refresh":
            await self.refresh_data()
        elif event.button.id == "stripe-setup":
            self.query_one("#stripe-status", Static).update(
                "Run: starter-cli stripe setup"
            )
        elif event.button.id == "stripe-webhook":
            self.query_one("#stripe-status", Static).update(
                "Run: starter-cli stripe webhook-secret"
            )

    async def refresh_data(self) -> None:
        snapshot = await asyncio.to_thread(self._load)
        self._env_values = snapshot.values
        table = self.query_one("#stripe-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Key", "Status", "Value")
        for key in REQUIRED_ENV_KEYS:
            value = self._env_values.get(key)
            status = "set" if value else "missing"
            display = mask_value(value)
            if key == "STRIPE_PRODUCT_PRICE_MAP" and value:
                display = "configured"
            table.add_row(key, status, display)
        enable_billing = snapshot.enable_billing
        if enable_billing:
            table.add_row("ENABLE_BILLING", "set", enable_billing)
        self.query_one("#stripe-status", Static).update("Stripe status loaded.")

    def _load(self) -> StripeStatus:
        return self.hub.load_stripe()


__all__ = ["StripePane"]
