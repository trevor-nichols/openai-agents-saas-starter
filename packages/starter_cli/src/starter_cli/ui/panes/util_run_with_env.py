from __future__ import annotations

import asyncio
import shlex
from dataclasses import dataclass
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Static

from starter_cli.core import CLIContext
from starter_cli.services.infra.ops_commands import CommandResult, run_command
from starter_cli.services.infra.run_with_env import RunWithEnvPlan, prepare_run_with_env
from starter_cli.ui.action_runner import ActionResult, ActionRunner
from starter_cli.ui.panes.command_output import format_command_result


@dataclass(slots=True)
class UtilRunResult:
    plan: RunWithEnvPlan
    command_result: CommandResult


class UtilRunWithEnvPane(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="util-run-with-env", classes="section-pane")
        self.ctx = ctx
        self._runner: ActionRunner[UtilRunResult] = ActionRunner(
            ctx=self.ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_complete=self._handle_complete,
            on_state_change=self._set_action_state,
        )

    def compose(self) -> ComposeResult:
        yield Static("Run With Env", classes="section-title")
        yield Static(
            "Merge env files and execute a command with the combined environment.",
            classes="section-description",
        )
        with Horizontal(classes="ops-actions"):
            yield Static("Env tokens", classes="wizard-control-label")
            yield Input(
                id="util-env-tokens",
                placeholder=".env .env.local KEY=VALUE",
            )
        with Horizontal(classes="ops-actions"):
            yield Static("Command", classes="wizard-control-label")
            yield Input(id="util-command", placeholder="echo hello")
        with Horizontal(classes="ops-actions"):
            yield Button("Preview", id="util-preview", variant="primary")
            yield Button("Run Command", id="util-run")
            yield Button("Reset", id="util-reset")
        yield Static("", id="util-status", classes="section-footnote")
        yield Static("", id="util-output", classes="ops-output")

    def on_mount(self) -> None:
        self.set_interval(0.4, self._runner.refresh_output)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "util-preview":
            self._preview()
        elif event.button.id == "util-run":
            self._run_command()
        elif event.button.id == "util-reset":
            self._reset()

    def _preview(self) -> None:
        try:
            plan = self._build_plan()
        except Exception as exc:  # CLIError + parsing
            self._set_status(str(exc))
            return
        self._set_output(self._render_preview(plan))
        self._set_status("Preview ready.")

    def _run_command(self) -> None:
        try:
            plan = self._build_plan()
        except Exception as exc:  # CLIError + parsing
            self._set_status(str(exc))
            return

        def _runner(ctx: CLIContext) -> UtilRunResult:
            ctx.console.info(
                f"Running command: {' '.join(plan.command)}",
                topic="util",
            )
            result = asyncio.run(
                run_command(
                    command=plan.command,
                    cwd=ctx.project_root,
                    env=plan.merged_env,
                )
            )
            return UtilRunResult(plan=plan, command_result=result)

        if not self._runner.start("Run with env", _runner):
            self._set_status("Run-with-env already running.")

    def _handle_complete(self, result: ActionResult[UtilRunResult]) -> None:
        if result.error or result.value is None:
            return
        if isinstance(result.value, UtilRunResult):
            output = format_command_result("Command", result.value.command_result)
            self._set_output(output)
            self._set_status("Command finished.")

    def _build_plan(self) -> RunWithEnvPlan:
        env_tokens = self._parse_tokens(self.query_one("#util-env-tokens", Input).value)
        command_tokens = self._parse_tokens(self.query_one("#util-command", Input).value)
        return prepare_run_with_env(env_tokens, command_tokens)

    def _render_preview(self, plan: RunWithEnvPlan) -> str:
        file_tokens = [token for token in plan.env_files if "=" not in token]
        inline_tokens = [token for token in plan.env_files if "=" in token]
        lines = [
            f"Command: {' '.join(plan.command)}",
            f"Env files: {', '.join(file_tokens) if file_tokens else '—'}",
        ]
        if file_tokens:
            for token in file_tokens:
                path = Path(token).expanduser()
                status = "found" if path.is_file() else "missing"
                lines.append(f"- {path} ({status})")
        if inline_tokens:
            lines.append(f"Inline overrides: {', '.join(inline_tokens)}")
        if plan.overrides:
            lines.append("Merged env keys:")
            for key in sorted(plan.overrides.keys()):
                value = plan.overrides[key]
                masked = "" if value == "" else "***"
                lines.append(f"- {key}={masked}")
        return "\n".join(lines)

    def _reset(self) -> None:
        self.query_one("#util-env-tokens", Input).value = ""
        self.query_one("#util-command", Input).value = ""
        self._set_output("")
        self._set_status("Cleared run-with-env inputs.")

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#util-preview", Button).disabled = running
        self.query_one("#util-run", Button).disabled = running
        self.query_one("#util-reset", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#util-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#util-output", Static).update(message)

    @staticmethod
    def _parse_tokens(raw: str) -> list[str]:
        if not raw:
            return []
        cleaned = " ".join(raw.replace(",", " ").splitlines())
        return [token for token in shlex.split(cleaned) if token]


__all__ = ["UtilRunWithEnvPane"]
