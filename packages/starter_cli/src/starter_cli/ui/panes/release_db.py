from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Static, Switch

from starter_cli.core import CLIContext
from starter_cli.services.infra.release_db import DatabaseReleaseConfig, DatabaseReleaseWorkflow
from starter_cli.ui.action_runner import ActionResult, ActionRunner


@dataclass(slots=True)
class ReleaseRunResult:
    summary_path: Path
    exit_code: int


class ReleaseDbPane(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="release-db", classes="section-pane")
        self.ctx = ctx
        self._runner = ActionRunner(
            ctx=self.ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_complete=self._handle_complete,
            on_state_change=self._set_action_state,
        )

    def compose(self) -> ComposeResult:
        yield Static("Release DB", classes="section-title")
        yield Static(
            "Run migrations, Stripe seeding, and billing plan checks.",
            classes="section-description",
        )
        with Horizontal(classes="ops-actions"):
            yield Static("Non-interactive", classes="wizard-control-label")
            yield Switch(value=False, id="release-non-interactive")
            yield Static("Skip Stripe", classes="wizard-control-label")
            yield Switch(value=False, id="release-skip-stripe")
            yield Static("Skip DB checks", classes="wizard-control-label")
            yield Switch(value=False, id="release-skip-db")
            yield Button("Run Release", id="release-run", variant="primary")
        with Horizontal(classes="ops-actions"):
            yield Static("Summary path", classes="wizard-control-label")
            yield Input(id="release-summary-path")
            yield Static("Plan overrides", classes="wizard-control-label")
            yield Input(id="release-plan-overrides", placeholder="starter=2500, pro=9900")
        yield DataTable(id="release-steps", zebra_stripes=True)
        yield DataTable(id="release-plans", zebra_stripes=True)
        yield Static("", id="release-status", classes="section-footnote")
        yield Static("", id="release-output", classes="ops-output")

    def on_mount(self) -> None:
        self.set_interval(0.4, self._runner.refresh_output)
        self._render_steps([])
        self._render_plans([])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "release-run":
            self._run_release()

    def _run_release(self) -> None:
        config = DatabaseReleaseConfig(
            non_interactive=self.query_one("#release-non-interactive", Switch).value,
            skip_stripe=self.query_one("#release-skip-stripe", Switch).value,
            skip_db_checks=self.query_one("#release-skip-db", Switch).value,
            json_output=False,
            summary_path=self._text_value("release-summary-path") or None,
            plan_overrides=self._split_list("release-plan-overrides") or None,
        )

        def _runner(ctx: CLIContext) -> ReleaseRunResult:
            workflow = DatabaseReleaseWorkflow(ctx=ctx, config=config)
            exit_code = workflow.run()
            return ReleaseRunResult(summary_path=workflow.summary_path, exit_code=exit_code)

        if not self._runner.start("Release DB", _runner):
            self._set_status("Release already running.")

    def _handle_complete(self, result: ActionResult[ReleaseRunResult]) -> None:
        if result.error or result.value is None:
            return
        summary_path = result.value.summary_path
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._set_status(f"Failed to read summary: {exc}")
            return
        self._render_steps(payload.get("steps", []))
        self._render_plans(payload.get("billing_plans", []))
        status = payload.get("status", "unknown")
        self._set_status(f"Release completed with status: {status} (summary: {summary_path})")

    def _render_steps(self, steps: list[dict[str, object]]) -> None:
        table = self.query_one("#release-steps", DataTable)
        table.clear(columns=True)
        table.add_columns("Step", "Status", "Detail")
        if not steps:
            table.add_row("-", "-", "No steps recorded yet")
            return
        for step in steps:
            table.add_row(
                str(step.get("name", "-")),
                str(step.get("status", "-")),
                str(step.get("detail", "")),
            )

    def _render_plans(self, plans: list[dict[str, object]]) -> None:
        table = self.query_one("#release-plans", DataTable)
        table.clear(columns=True)
        table.add_columns("Plan", "Status", "Price ID", "Active")
        if not plans:
            table.add_row("-", "-", "-", "-")
            return
        for plan in plans:
            table.add_row(
                str(plan.get("code", "-")),
                str(plan.get("status", "-")),
                str(plan.get("stripe_price_id", "-")),
                str(plan.get("is_active", False)),
            )

    def _text_value(self, input_id: str) -> str:
        return self.query_one(f"#{input_id}", Input).value.strip()

    def _split_list(self, input_id: str) -> list[str]:
        raw = self._text_value(input_id)
        if not raw:
            return []
        parts = [part.strip() for part in raw.replace(";", ",").split(",")]
        return [part for part in parts if part]

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#release-run", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#release-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#release-output", Static).update(message)


__all__ = ["ReleaseDbPane"]
