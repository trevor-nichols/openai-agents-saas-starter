from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Grid
from textual.timer import Timer
from textual.widgets import Button, Collapsible, DataTable, Input, Static, Switch

from starter_console.core import CLIContext
from starter_console.services.infra.logs_ops import (
    DEFAULT_LINES,
    ArchiveLogsConfig,
    TailStream,
    archive_logs,
    plan_targets,
    start_stream,
    stop_streams,
)
from starter_console.services.infra.ops_commands import run_command
from starter_console.services.infra.ops_models import LogEntry
from starter_console.ui.action_runner import ActionRunner
from starter_console.ui.buffer_console import BufferConsole
from starter_console.workflows.home.hub import HubService

from .command_output import format_command_result
from .footer_pane import FooterPane


class LogsPane(FooterPane):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(pane_id="logs")
        self.ctx = ctx
        self.hub = hub
        self._log_root: Path | None = None
        self._log_dir: Path | None = None
        self._entries: list[LogEntry] = []
        self._follow_timer: Timer | None = None
        self._follow_streams: list[TailStream] = []
        self._follow_notes: list[str] = []
        self._follow_console: BufferConsole | None = None
        self._follow_errors: list[str] = []
        self._archive_runner: ActionRunner[int] = ActionRunner(
            ctx=self.ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_state_change=self._set_action_state,
        )

    def compose_body(self) -> ComposeResult:
        yield Static("Logs", classes="section-title")
        yield Static("", id="logs-summary", classes="section-summary")
        with Collapsible(title="Tail options", id="logs-tail-options", collapsed=True):
            with Grid(classes="form-grid"):
                yield Static("Services", classes="wizard-control-label")
                yield Input(
                    id="logs-services",
                    placeholder="all, api, frontend, starter-console, collector, postgres, redis",
                )
                yield Static("Lines", classes="wizard-control-label")
                yield Input(id="logs-lines", value="")
                yield Static("Errors only", classes="wizard-control-label")
                yield Switch(value=False, id="logs-errors")
                yield Static("Follow", classes="wizard-control-label")
                yield Switch(value=True, id="logs-follow")
                yield Static("Log root", classes="wizard-control-label")
                yield Input(id="logs-log-root", placeholder="var/log")
        with Collapsible(title="Archive options", id="logs-archive-options", collapsed=True):
            with Grid(classes="form-grid"):
                yield Static("Days", classes="wizard-control-label")
                yield Input(id="logs-archive-days", value="7")
                yield Static("Dry run", classes="wizard-control-label")
                yield Switch(value=False, id="logs-archive-dry-run")
        yield DataTable(id="logs-table", zebra_stripes=True)
        yield Static("", id="logs-output", classes="ops-output")

    def compose_footer(self) -> ComposeResult:
        yield Button("Refresh", id="logs-refresh", variant="primary")
        yield Button("Tail", id="logs-tail")
        yield Button("Stop Follow", id="logs-stop-follow")
        yield Button("Archive", id="logs-archive")
        yield self.footer_spacer()
        yield Static("", id="logs-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()
        self.set_interval(0.4, self._archive_runner.refresh_output)

    def on_hide(self) -> None:
        self._stop_follow(clear_status=False)

    def on_unmount(self) -> None:
        self._stop_follow(clear_status=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "logs-refresh":
            await self.refresh_data()
        elif event.button.id == "logs-tail":
            if self._follow_enabled():
                self._start_follow()
            else:
                await self._tail_now()
        elif event.button.id == "logs-stop-follow":
            self._stop_follow()
        elif event.button.id == "logs-archive":
            self._run_archive()

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
        self.query_one("#logs-status", Static).update("Ready to tail logs or archive history.")

    async def _tail_now(self) -> None:
        self._stop_follow(clear_status=False)
        self._set_status("Collecting log output…")
        output = await self._collect_tail_output()
        self._set_output(output)
        self._set_status("Tail complete.")

    async def _collect_tail_output(self) -> str:
        services = self._parse_services()
        lines = self._parse_int("logs-lines", default=DEFAULT_LINES)
        errors_only = self.query_one("#logs-errors", Switch).value
        log_root_override = self._log_root_override()

        buffer = BufferConsole()
        env = self._build_env_override(log_root_override)

        targets, notes = await asyncio.to_thread(
            plan_targets,
            self.ctx,
            services,
            lines=lines,
            follow=False,
            errors_only=errors_only,
            console=buffer,
            env=env,
        )
        lines_out: list[str] = []
        for level, message in notes:
            lines_out.append(f"{level.upper()}: {message}")
        for note in buffer.messages:
            lines_out.append(note)

        if not targets:
            lines_out.append("No log targets available for the selected services.")
            return "\n".join(lines_out)

        for target in targets:
            result = await run_command(command=target.command, cwd=target.cwd)
            header = f"[{target.name}] {' '.join(target.command)}"
            lines_out.append(header)
            lines_out.append(format_command_result(target.name, result))
            lines_out.append("")
        return "\n".join(lines_out).strip()

    def _run_archive(self) -> None:
        days = self._parse_int("logs-archive-days", default=7)
        dry_run = self.query_one("#logs-archive-dry-run", Switch).value
        log_root_override = self._log_root_override()
        args = argparse.Namespace(
            days=days,
            log_root=Path(log_root_override) if log_root_override else None,
            dry_run=dry_run,
        )

        def _runner(ctx: CLIContext) -> int:
            config = ArchiveLogsConfig(
                days=args.days,
                log_root=args.log_root,
                dry_run=args.dry_run,
            )
            return archive_logs(ctx, config)

        if not self._archive_runner.start("Archive logs", _runner):
            self._set_status("Archive already running.")

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#logs-archive", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#logs-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#logs-output", Static).update(message)

    def _parse_services(self) -> list[str]:
        raw = self.query_one("#logs-services", Input).value.strip()
        if not raw:
            return ["all"]
        parts = [part.strip() for part in raw.replace(";", ",").split(",")]
        return [part for part in parts if part]

    def _parse_int(self, input_id: str, *, default: int) -> int:
        raw = self.query_one(f"#{input_id}", Input).value.strip()
        if not raw:
            return default
        try:
            return max(int(raw), 1)
        except ValueError:
            self._set_status(f"Invalid value for {input_id}; using {default}.")
            return default

    def _log_root_override(self) -> str | None:
        raw = self.query_one("#logs-log-root", Input).value.strip()
        return raw or None

    def _follow_enabled(self) -> bool:
        return self.query_one("#logs-follow", Switch).value

    def _start_follow(self) -> None:
        if self._follow_timer is not None:
            return
        self._stop_follow(clear_status=False)
        self._set_status("Starting follow mode…")
        services = self._parse_services()
        lines = self._parse_int("logs-lines", default=DEFAULT_LINES)
        errors_only = self.query_one("#logs-errors", Switch).value
        log_root_override = self._log_root_override()
        buffer = BufferConsole(max_lines=500)

        env = self._build_env_override(log_root_override)
        targets, notes = plan_targets(
            self.ctx,
            services,
            lines=lines,
            follow=True,
            errors_only=errors_only,
            console=buffer,
            env=env,
        )

        if not targets:
            self._set_output("No log targets available for the selected services.")
            self._set_status("Follow aborted (no targets).")
            return

        startup_messages = list(buffer.snapshot())
        buffer.clear()
        self._follow_console = buffer
        self._follow_notes = [
            *[f"{level.upper()}: {message}" for level, message in notes],
            *startup_messages,
        ]
        self._follow_errors = []
        self._follow_streams = []

        for target in targets:
            stream = start_stream(buffer, target, self._follow_errors)
            if stream is not None:
                self._follow_streams.append(stream)

        if not self._follow_streams:
            self._set_output("No log streams could be started for the selected services.")
            self._set_status("Follow aborted (stream start failed).")
            return

        self._refresh_follow_output()
        self._set_status("Following logs (streaming).")
        self._follow_timer = self.set_interval(0.5, self._refresh_follow_output)

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
        self._follow_notes = []
        self._follow_console = None
        self._follow_errors = []
        if clear_status:
            self._set_status("Stopped follow mode.")

    @staticmethod
    def _build_env_override(log_root_override: str | None) -> dict[str, str] | None:
        if not log_root_override:
            return None
        return {**os.environ, "LOG_ROOT": log_root_override}


__all__ = ["LogsPane"]
