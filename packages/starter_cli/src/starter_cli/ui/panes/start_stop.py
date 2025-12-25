from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, RadioButton, RadioSet, Static, Switch

from starter_cli.core import CLIContext
from starter_cli.services.infra.stack_ops import stop_stack
from starter_cli.ui.action_runner import ActionResult, ActionRunner
from starter_cli.workflows.home.stack_state import STACK_STATE_PATH, load, status
from starter_cli.workflows.home.start import StartRunner


class StartStopPane(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="start-stop", classes="section-pane")
        self.ctx = ctx
        self._runner = ActionRunner(
            ctx=self.ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_complete=self._handle_complete,
            on_state_change=self._set_action_state,
        )
        self._refresh_task: asyncio.Task[None] | None = None

    def compose(self) -> ComposeResult:
        yield Static("Start / Stop", classes="section-title")
        yield Static("Run local services or stop managed stacks.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Static("Target", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Dev", id="start-target-dev"),
                RadioButton("Backend", id="start-target-backend"),
                RadioButton("Frontend", id="start-target-frontend"),
                id="start-target",
            )
            yield Static("Mode", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Foreground", id="start-mode-foreground"),
                RadioButton("Detached", id="start-mode-detached"),
                id="start-mode",
            )
            yield Static("Open browser", classes="wizard-control-label")
            yield Switch(value=False, id="start-open-browser")
            yield Static("Skip infra", classes="wizard-control-label")
            yield Switch(value=False, id="start-skip-infra")
            yield Static("Force", classes="wizard-control-label")
            yield Switch(value=False, id="start-force")
            yield Button("Start", id="start-run", variant="primary")
            yield Button("Stop", id="start-stop")
            yield Button("Refresh Status", id="start-refresh")
        with Horizontal(classes="ops-actions"):
            yield Static("Timeout (s)", classes="wizard-control-label")
            yield Input(id="start-timeout", value="120")
            yield Static("Log dir", classes="wizard-control-label")
            yield Input(id="start-log-dir", placeholder="var/log")
            yield Static("Pidfile", classes="wizard-control-label")
            yield Input(id="start-pidfile", placeholder=str(STACK_STATE_PATH))
        yield DataTable(id="start-status", zebra_stripes=True)
        yield Static("", id="start-summary", classes="section-summary")
        yield Static("", id="start-status-text", classes="section-footnote")
        yield Static("", id="start-output", classes="ops-output")

    async def on_mount(self) -> None:
        self.query_one("#start-target-dev", RadioButton).value = True
        self.query_one("#start-mode-foreground", RadioButton).value = True
        self.set_interval(0.4, self._runner.refresh_output)
        await self.refresh_status()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-run":
            self._run_start()
        elif event.button.id == "start-stop":
            self._run_stop()
        elif event.button.id == "start-refresh":
            await self.refresh_status()

    async def refresh_status(self) -> None:
        await asyncio.to_thread(self._render_status)

    def _render_status(self) -> None:
        pidfile = self._pidfile()
        state = load(pidfile) if pidfile else None
        snapshot = status(state)
        table = self.query_one("#start-status", DataTable)
        table.clear(columns=True)
        table.add_columns("Label", "PID", "Status", "Log Path")
        for proc in snapshot.running:
            table.add_row(proc.label, str(proc.pid), "running", proc.log_path or "-")
        for proc in snapshot.dead:
            table.add_row(proc.label, str(proc.pid), "dead", proc.log_path or "-")
        if not snapshot.running and not snapshot.dead:
            table.add_row("-", "-", "stopped", "-")
        summary = f"Stack state: {snapshot.state}"
        if snapshot.log_dir:
            summary += f" | logs: {snapshot.log_dir}"
        if snapshot.infra_started:
            summary += " | infra: started"
        self.query_one("#start-summary", Static).update(summary)

    def _run_start(self) -> None:
        target = self._selected_target()
        detach = self._selected_mode() == "detached"
        timeout = self._int_value("start-timeout", default=120)
        open_browser = self.query_one("#start-open-browser", Switch).value
        skip_infra = self.query_one("#start-skip-infra", Switch).value
        force = self.query_one("#start-force", Switch).value
        log_dir = self._path_value("start-log-dir")
        pidfile = self._pidfile()

        def _runner(ctx: CLIContext) -> int:
            runner = StartRunner(
                ctx,
                target=target,
                timeout=float(timeout),
                open_browser=open_browser,
                skip_infra=skip_infra,
                detach=detach,
                force=force,
                pidfile=pidfile,
                log_dir=log_dir,
            )
            return runner.run()

        if not self._runner.start("Start stack", _runner):
            self._set_status("Start already running.")

    def _run_stop(self) -> None:
        args = argparse.Namespace(pidfile=self._pidfile())

        def _runner(ctx: CLIContext) -> int:
            stop_stack(ctx, pidfile=args.pidfile)
            return 0

        if not self._runner.start("Stop stack", _runner):
            self._set_status("Stop already running.")

    def _handle_complete(self, _: ActionResult[int]) -> None:
        self._refresh_task = asyncio.create_task(self.refresh_status())

    def _selected_target(self) -> str:
        radio = self.query_one("#start-target", RadioSet)
        selected = radio.pressed_button
        if selected is None or selected.id is None:
            return "dev"
        if selected.id.endswith("backend"):
            return "backend"
        if selected.id.endswith("frontend"):
            return "frontend"
        return "dev"

    def _selected_mode(self) -> str:
        radio = self.query_one("#start-mode", RadioSet)
        selected = radio.pressed_button
        if selected is None or selected.id is None:
            return "foreground"
        return "detached" if selected.id.endswith("detached") else "foreground"

    def _path_value(self, input_id: str) -> Path | None:
        raw = self.query_one(f"#{input_id}", Input).value.strip()
        if not raw:
            return None
        return Path(raw).expanduser().resolve()

    def _pidfile(self) -> Path | None:
        raw = self.query_one("#start-pidfile", Input).value.strip()
        if not raw:
            return None
        return Path(raw).expanduser().resolve()

    def _int_value(self, input_id: str, *, default: int) -> int:
        raw = self.query_one(f"#{input_id}", Input).value.strip()
        if not raw:
            return default
        try:
            return max(int(raw), 1)
        except ValueError:
            self._set_status(f"Invalid value for {input_id}; using {default}.")
            return default

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#start-run", Button).disabled = running
        self.query_one("#start-stop", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#start-status-text", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#start-output", Static).update(message)


__all__ = ["StartStopPane"]
