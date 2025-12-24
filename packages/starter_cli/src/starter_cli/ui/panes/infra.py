from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from starter_cli.core import CLIContext
from starter_cli.services.infra import DependencyStatus
from starter_cli.services.ops_commands import run_command
from starter_cli.workflows.home.hub import HubService

from .command_output import format_command_result


class InfraPane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="infra", classes="section-pane")
        self.ctx = ctx
        self.hub = hub
        self._deps: list[DependencyStatus] = []

    def compose(self) -> ComposeResult:
        yield Static("Infra", classes="section-title")
        yield Static("Local tooling and compose helpers.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Button("Refresh", id="infra-refresh", variant="primary")
            yield Button("Compose Up", id="infra-compose-up")
            yield Button("Compose Down", id="infra-compose-down")
            yield Button("Vault Up", id="infra-vault-up")
            yield Button("Vault Down", id="infra-vault-down")
        yield DataTable(id="infra-deps", zebra_stripes=True)
        yield Static("", id="infra-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "infra-refresh":
            await self.refresh_data()
        elif event.button.id == "infra-compose-up":
            await self._run_just("dev-up")
        elif event.button.id == "infra-compose-down":
            await self._run_just("dev-down")
        elif event.button.id == "infra-vault-up":
            await self._run_just("vault-up")
        elif event.button.id == "infra-vault-down":
            await self._run_just("vault-down")

    async def refresh_data(self) -> None:
        self.query_one("#infra-status", Static).update("Refreshing dependency status...")
        snapshot = await asyncio.to_thread(self.hub.load_infra)
        self._deps = list(snapshot.dependencies)
        table = self.query_one("#infra-deps", DataTable)
        table.clear(columns=True)
        table.add_columns("Dependency", "Status", "Version", "Path", "Hint")
        for dep in self._deps:
            table.add_row(
                dep.name,
                dep.status,
                dep.version or "",
                dep.path or "",
                "" if dep.status == "ok" else dep.hint,
            )
        self.query_one("#infra-status", Static).update("Dependency check complete.")

    async def _run_just(self, target: str) -> None:
        status = self.query_one("#infra-status", Static)
        label = f"just {target}"
        status.update(f"Running {label}...")
        result = await run_command(command=["just", target], cwd=self.ctx.project_root)
        status.update(format_command_result(label, result))


__all__ = ["InfraPane"]
