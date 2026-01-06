from __future__ import annotations

import asyncio
import json

from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.timer import Timer
from textual.widgets import Button, DataTable, Static

from starter_console.core import CLIContext
from starter_console.services.infra import (
    DependencyStatus,
    just_command,
    resolve_compose_target,
    resolve_vault_target,
)
from starter_console.services.infra.logs_ops import (
    TailStream,
    TailTarget,
    start_stream,
    stop_streams,
)
from starter_console.services.infra.ops_commands import run_command
from starter_console.ui.buffer_console import BufferConsole
from starter_console.workflows.home.hub import HubService

from .command_output import format_command_result


class InfraPane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="infra", classes="section-pane footer-pane")
        self.ctx = ctx
        self.hub = hub
        self._deps: list[DependencyStatus] = []
        self._follow_timer: Timer | None = None
        self._follow_streams: list[TailStream] = []
        self._follow_console: BufferConsole | None = None
        self._follow_errors: list[str] = []
        self._follow_notes: list[str] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="infra-body", classes="pane-body"):
            yield Static("Infra", classes="section-title")
            yield Static("Local tooling and compose helpers.", classes="section-description")
            yield DataTable(id="infra-deps", zebra_stripes=True)
            yield Static("", id="infra-output", classes="ops-output")
        with Vertical(id="infra-footer", classes="pane-footer"):
            with Grid(id="infra-actions-grid", classes="infra-actions-grid"):
                yield Button("Refresh", id="infra-refresh", variant="primary")
                yield Button("Compose Up", id="infra-compose-up")
                yield Button("Compose Down", id="infra-compose-down")
                yield Button("Compose Logs", id="infra-compose-logs")
                yield Button("Compose PS", id="infra-compose-ps")
                yield Button("Deps JSON", id="infra-deps-json")
                yield Button("Vault Up", id="infra-vault-up")
                yield Button("Vault Down", id="infra-vault-down")
                yield Button("Vault Logs", id="infra-vault-logs")
                yield Button("Vault Verify", id="infra-vault-verify")
                yield Button("Stop Follow", id="infra-stop-follow")
            with Horizontal(id="infra-status-row", classes="infra-status-row"):
                yield Static("", classes="pane-footer-spacer")
                yield Static("", id="infra-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()

    def on_hide(self) -> None:
        self._stop_follow(clear_status=False)

    def on_unmount(self) -> None:
        self._stop_follow(clear_status=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "infra-refresh":
            await self.refresh_data()
        elif event.button.id == "infra-compose-up":
            await self._run_compose("up")
        elif event.button.id == "infra-compose-down":
            await self._run_compose("down")
        elif event.button.id == "infra-compose-logs":
            self._start_follow("compose logs", resolve_compose_target("logs"))
        elif event.button.id == "infra-compose-ps":
            await self._run_compose("ps")
        elif event.button.id == "infra-vault-up":
            await self._run_vault("up")
        elif event.button.id == "infra-vault-down":
            await self._run_vault("down")
        elif event.button.id == "infra-vault-logs":
            self._start_follow("vault logs", resolve_vault_target("logs"))
        elif event.button.id == "infra-vault-verify":
            await self._run_vault("verify")
        elif event.button.id == "infra-stop-follow":
            self._stop_follow()
        elif event.button.id == "infra-deps-json":
            self._render_deps_json()

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

    async def _run_compose(self, action: str) -> None:
        await self._run_just(resolve_compose_target(action))

    async def _run_vault(self, action: str) -> None:
        await self._run_just(resolve_vault_target(action))

    async def _run_just(self, target: str) -> None:
        status = self.query_one("#infra-status", Static)
        output = self.query_one("#infra-output", Static)
        label = f"just {target}"
        status.update(f"Running {label}...")
        output.update("")
        result = await run_command(command=just_command(target), cwd=self.ctx.project_root)
        message = format_command_result(label, result)
        output.update(message)
        status.update("Done.")

    def _start_follow(self, label: str, target: str) -> None:
        if self._follow_timer is not None:
            self._set_status("Already following logs; stop follow first.")
            return
        self._stop_follow(clear_status=False)
        command = just_command(target)
        buffer = BufferConsole(max_lines=500)
        self._follow_console = buffer
        self._follow_errors = []
        self._follow_notes = [f"$ {' '.join(command)}"]
        stream = start_stream(
            buffer,
            TailTarget(name=label, command=command, cwd=self.ctx.project_root),
            self._follow_errors,
        )
        if stream is None:
            self._set_status("Follow aborted (stream start failed).")
            self._set_output("Unable to start log streaming process.")
            self._follow_console = None
            return
        self._follow_streams = [stream]
        self._refresh_follow_output()
        self._follow_timer = self.set_interval(0.5, self._refresh_follow_output)
        self._set_status(f"Following {label}...")

    def _refresh_follow_output(self) -> None:
        if self._follow_console is None:
            return
        stream_lines = list(self._follow_console.snapshot())
        output_lines = self._follow_notes + stream_lines[-200:]
        if self._follow_errors:
            output_lines.append(
                f"ERROR: {self._follow_errors[-1]} (total {len(self._follow_errors)})"
            )
        self._set_output("\n".join(output_lines).strip())

    def _stop_follow(self, *, clear_status: bool = True) -> None:
        if self._follow_timer is not None:
            self._follow_timer.stop()
            self._follow_timer = None
        if self._follow_streams:
            stop_streams(self._follow_streams)
        self._follow_streams = []
        self._follow_console = None
        self._follow_errors = []
        self._follow_notes = []
        if clear_status:
            self._set_status("Stopped follow mode.")

    def _render_deps_json(self) -> None:
        deps = self._deps or []
        payload = [
            {
                "name": dep.name,
                "status": dep.status,
                "version": dep.version or "",
                "path": dep.path or "",
                "command": list(dep.command) if dep.command else None,
                "hint": dep.hint if dep.status != "ok" else "",
            }
            for dep in deps
        ]
        output = self.query_one("#infra-output", Static)
        output.update(json.dumps(payload, indent=2))
        self.query_one("#infra-status", Static).update("Exported dependency JSON snapshot.")

    def _set_status(self, message: str) -> None:
        self.query_one("#infra-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#infra-output", Static).update(message)


__all__ = ["InfraPane"]
