from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Protocol, runtime_checkable

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from starter_cli.core import CLIContext
from starter_cli.workflows.home.hub import HubService
from starter_cli.workflows.setup_menu.models import SetupAction, SetupItem

from ..view_models import setup_row


class SetupPane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService, *, stale_days: int) -> None:
        super().__init__(id="setup", classes="section-pane")
        self.ctx = ctx
        self.hub = hub
        self._items: list[SetupItem] = []
        self._stale_window = timedelta(days=stale_days)

    def compose(self) -> ComposeResult:
        yield Static("Setup Hub", classes="section-title")
        yield Static(
            "Guided setup actions for secrets, infra, and providers.",
            classes="section-description",
        )
        with Horizontal(classes="setup-actions"):
            yield Button("Refresh", id="setup-refresh", variant="primary")
            yield Button("Run Selected", id="setup-run")
        yield DataTable(id="setup-table", zebra_stripes=True)
        yield Static("", id="setup-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "setup-refresh":
            await self.refresh_data()
        elif event.button.id == "setup-run":
            await self._run_selected()

    async def refresh_data(self) -> None:
        self._set_status("Refreshing setup items...")
        await asyncio.to_thread(self._load_items)
        self._render_table()
        self._set_status("Select a row and choose Run Selected.")

    def _load_items(self) -> None:
        snapshot = self.hub.load_setup(stale_days=self._stale_window.days)
        self._items = list(snapshot.items)

    def _render_table(self) -> None:
        table = self.query_one("#setup-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Status", "Setup", "Detail", "Progress", "Last Run")
        for item in self._items:
            table.add_row(*setup_row(item), key=item.key)
        if table.row_count:
            table.focus()
            table.move_cursor(row=0, column=0)

    async def _run_selected(self) -> None:
        table = self.query_one("#setup-table", DataTable)
        if table.cursor_row is None:
            self._set_status("Choose a setup row first.")
            return
        if table.cursor_row < 0 or table.cursor_row >= len(self._items):
            self._set_status("Selection out of range.")
            return
        item = self._items[table.cursor_row]
        if not item.actions:
            self._set_status("No actions available for this setup item.")
            return
        await self._run_action(item.actions[0])
        await self.refresh_data()

    async def _run_action(self, action: SetupAction) -> None:
        if action.key == "secrets_onboard":
            if self._open_secrets_onboard():
                return
        if action.route:
            if self._navigate(action.route):
                self._set_status(f"Opened {action.label}.")
                return
        if action.command:
            self._set_status(f"Run: {' '.join(action.command)}")
            return
        self._set_status("No action available for this item.")

    def _set_status(self, message: str) -> None:
        self.query_one("#setup-status", Static).update(message)

    def _navigate(self, route: str) -> bool:
        app = self.app
        if isinstance(app, _Navigator):
            app.action_go(route)
            return True
        return False

    def _open_secrets_onboard(self) -> bool:
        app = self.app
        if isinstance(app, _SecretsLauncher):
            app.open_secrets_onboard()
            return True
        return False


@runtime_checkable
class _Navigator(Protocol):
    def action_go(self, section_key: str) -> None: ...


@runtime_checkable
class _SecretsLauncher(Protocol):
    def open_secrets_onboard(self) -> None: ...


__all__ = ["SetupPane"]
