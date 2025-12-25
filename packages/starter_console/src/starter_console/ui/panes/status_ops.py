from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, RadioButton, RadioSet, Static

from starter_console.core import CLIContext
from starter_console.services.auth.status_ops import StatusOpsClient, StatusSubscription
from starter_console.ui.action_runner import ActionResult, ActionRunner


@dataclass(slots=True)
class StatusListResult:
    items: list[StatusSubscription]
    next_cursor: str | None


@dataclass(slots=True)
class StatusRevokeResult:
    subscription_id: str


@dataclass(slots=True)
class StatusIncidentResult:
    incident_id: str
    dispatched: int


StatusActionResult = StatusListResult | StatusRevokeResult | StatusIncidentResult


class StatusOpsPane(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="status-ops", classes="section-pane")
        self.ctx = ctx
        self._runner: ActionRunner[StatusActionResult] = ActionRunner(
            ctx=self.ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_complete=self._handle_complete,
            on_state_change=self._set_action_state,
        )
        self._subscriptions: list[StatusSubscription] = []

    def compose(self) -> ComposeResult:
        yield Static("Status Ops", classes="section-title")
        yield Static(
            "Manage status subscriptions and resend incident notifications.",
            classes="section-description",
        )
        with Horizontal(classes="ops-actions"):
            yield Static("Limit", classes="wizard-control-label")
            yield Input(id="status-limit", value="50")
            yield Static("Cursor", classes="wizard-control-label")
            yield Input(id="status-cursor")
            yield Static("Tenant", classes="wizard-control-label")
            yield Input(id="status-tenant")
            yield Button("List Subscriptions", id="status-list", variant="primary")
        with Horizontal(classes="ops-actions"):
            yield Static("Subscription ID", classes="wizard-control-label")
            yield Input(id="status-subscription-id")
            yield Button("Revoke Subscription", id="status-revoke")
        with Horizontal(classes="ops-actions"):
            yield Static("Incident ID", classes="wizard-control-label")
            yield Input(id="status-incident-id")
            yield Static("Severity", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("All", id="status-severity-all"),
                RadioButton("Major", id="status-severity-major"),
                RadioButton("Maintenance", id="status-severity-maintenance"),
                id="status-severity",
            )
            yield Static("Tenant", classes="wizard-control-label")
            yield Input(id="status-incident-tenant")
            yield Button("Resend Incident", id="status-resend")
        yield DataTable(id="status-table", zebra_stripes=True)
        yield Static("", id="status-status", classes="section-footnote")
        yield Static("", id="status-output", classes="ops-output")

    def on_mount(self) -> None:
        self.query_one("#status-severity-major", RadioButton).value = True
        self.set_interval(0.4, self._runner.refresh_output)
        self._render_table([])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "status-list":
            self._run_list()
        elif event.button.id == "status-revoke":
            self._run_revoke()
        elif event.button.id == "status-resend":
            self._run_resend()

    def _run_list(self) -> None:
        limit = self._parse_int("#status-limit", default=50)
        if limit is None:
            return
        cursor = self._read_input("#status-cursor")
        tenant = self._read_input("#status-tenant")

        def _runner(ctx: CLIContext) -> StatusListResult:
            client = StatusOpsClient.from_env()
            result = client.list_subscriptions(limit=limit, cursor=cursor, tenant_id=tenant)
            ctx.console.info(
                f"Fetched {len(result.items)} subscriptions.",
                topic="status",
            )
            return StatusListResult(items=result.items, next_cursor=result.next_cursor)

        if not self._runner.start("List subscriptions", _runner):
            self._set_status("Status ops already running.")

    def _run_revoke(self) -> None:
        subscription_id = self._read_input("#status-subscription-id")
        if not subscription_id:
            self._set_status("Subscription ID is required to revoke.")
            return

        def _runner(ctx: CLIContext) -> StatusRevokeResult:
            client = StatusOpsClient.from_env()
            client.revoke_subscription(subscription_id)
            ctx.console.success(
                f"Subscription {subscription_id} revoked.",
                topic="status",
            )
            return StatusRevokeResult(subscription_id=subscription_id)

        if not self._runner.start("Revoke subscription", _runner):
            self._set_status("Status ops already running.")

    def _run_resend(self) -> None:
        incident_id = self._read_input("#status-incident-id")
        if not incident_id:
            self._set_status("Incident ID is required to resend.")
            return
        severity = self._selected_severity()
        tenant = self._read_input("#status-incident-tenant")

        def _runner(ctx: CLIContext) -> StatusIncidentResult:
            client = StatusOpsClient.from_env()
            result = client.resend_incident(
                incident_id=incident_id,
                severity=severity,
                tenant_id=tenant or None,
            )
            ctx.console.success(
                f"Incident {incident_id} dispatched to {result.dispatched} subscription(s).",
                topic="status",
            )
            return StatusIncidentResult(
                incident_id=incident_id,
                dispatched=result.dispatched,
            )

        if not self._runner.start("Resend incident", _runner):
            self._set_status("Status ops already running.")

    def _handle_complete(self, result: ActionResult[StatusActionResult]) -> None:
        if result.error or result.value is None:
            return
        if isinstance(result.value, StatusListResult):
            self._subscriptions = result.value.items
            self._render_table(self._subscriptions)
            if result.value.next_cursor:
                self.query_one("#status-cursor", Input).value = result.value.next_cursor
                self._set_status("Loaded subscriptions; next cursor set.")
            else:
                self._set_status("Loaded subscriptions.")
            return
        if isinstance(result.value, StatusRevokeResult):
            self._set_status(f"Subscription {result.value.subscription_id} revoked.")
            return
        if isinstance(result.value, StatusIncidentResult):
            self._set_status(
                f"Incident {result.value.incident_id} resent "
                f"({result.value.dispatched} dispatched)."
            )

    def _render_table(self, items: list[StatusSubscription]) -> None:
        table = self.query_one("#status-table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Status", "Channel", "Severity", "Target", "Tenant")
        for item in items:
            table.add_row(
                item.id,
                item.status,
                item.channel,
                item.severity_filter,
                item.target_masked,
                item.tenant_id or "—",
            )

    def _parse_int(self, input_id: str, *, default: int) -> int | None:
        raw = self._read_input(input_id)
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError:
            self._set_status("Limit must be a number.")
            return None
        if value <= 0:
            self._set_status("Limit must be greater than 0.")
            return None
        return value

    def _read_input(self, input_id: str) -> str:
        return self.query_one(input_id, Input).value.strip()

    def _selected_severity(self) -> str:
        radio = self.query_one("#status-severity", RadioSet)
        selected = radio.pressed_button
        if selected is None or selected.id is None:
            return "major"
        if selected.id.endswith("all"):
            return "all"
        if selected.id.endswith("maintenance"):
            return "maintenance"
        return "major"

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#status-list", Button).disabled = running
        self.query_one("#status-revoke", Button).disabled = running
        self.query_one("#status-resend", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#status-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#status-output", Static).update(message)


__all__ = ["StatusOpsPane"]
