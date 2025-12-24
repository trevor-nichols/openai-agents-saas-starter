from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from starter_cli.core import CLIContext
from starter_cli.services.ops_commands import run_command
from starter_cli.services.ops_models import LogEntry
from starter_cli.workflows.home.hub import HubService

from .command_output import format_command_result


class LogsPane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="logs", classes="section-pane")
        self.ctx = ctx
        self.hub = hub
        self._log_root: Path | None = None
        self._log_dir: Path | None = None
        self._entries: list[LogEntry] = []

    def compose(self) -> ComposeResult:
        yield Static("Logs", classes="section-title")
        yield Static("", id="logs-summary", classes="section-summary")
        with Horizontal(classes="ops-actions"):
            yield Button("Refresh", id="logs-refresh", variant="primary")
            yield Button("Tail API", id="logs-tail-api")
            yield Button("Tail API Errors", id="logs-tail-errors")
            yield Button("Tail CLI", id="logs-tail-cli")
        yield DataTable(id="logs-table", zebra_stripes=True)
        yield Static("", id="logs-status", classes="section-footnote")
        yield Static("", id="logs-output", classes="ops-output")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "logs-refresh":
            await self.refresh_data()
        elif event.button.id == "logs-tail-api":
            await self._tail_entry("api/all.log")
        elif event.button.id == "logs-tail-errors":
            await self._tail_entry("api/error.log")
        elif event.button.id == "logs-tail-cli":
            await self._tail_entry("cli/*.log")

    async def refresh_data(self) -> None:
        await asyncio.to_thread(self._collect)
        self._render_table()

    def _collect(self) -> None:
        snapshot = self.hub.load_logs()
        self._log_root = snapshot.log_root
        self._log_dir = snapshot.log_dir
        self._entries = list(snapshot.entries)

    def _render_table(self) -> None:
        table = self.query_one("#logs-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Target", "Path", "Status")
        for entry in self._entries:
            status = "present" if entry.exists else "missing"
            table.add_row(entry.name, str(entry.path), status)
        summary = f"Log root: {self._log_root} | Active dir: {self._log_dir}"
        self.query_one("#logs-summary", Static).update(summary)
        self.query_one("#logs-status", Static).update("Select a Tail action to preview logs.")

    async def _tail_entry(self, name: str) -> None:
        entry = next((item for item in self._entries if item.name == name), None)
        if entry is None:
            self.query_one("#logs-status", Static).update(f"No log entry named {name}.")
            return
        target = entry.path
        if target.is_dir():
            candidates = sorted(
                target.glob("*.log"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            if not candidates:
                self.query_one("#logs-status", Static).update("No CLI log files found.")
                return
            target = candidates[0]
        if not target.exists():
            self.query_one("#logs-status", Static).update(f"Missing log file: {target}")
            return
        await self._run_command(
            self.query_one("#logs-output", Static),
            command=["tail", "-n", "200", str(target)],
            label=f"tail {name}",
        )

    async def _run_command(self, output: Static, *, command: list[str], label: str) -> None:
        output.update(f"Running {label}...")
        result = await run_command(command=command, cwd=self.ctx.project_root)
        output.update(format_command_result(label, result))


__all__ = ["LogsPane"]
