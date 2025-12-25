from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, RadioButton, RadioSet, Static, Switch

from starter_cli.core import CLIContext, CLIError
from starter_cli.services.auth.tokens import (
    IssueServiceAccountRequest,
    issue_service_account,
    parse_scopes,
    render_issue_output,
    resolve_base_url,
    resolve_output_format,
)
from starter_cli.ui.action_runner import ActionResult, ActionRunner


class AuthTokensPane(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="auth-tokens", classes="section-pane")
        self.ctx = ctx
        self._runner = ActionRunner(
            ctx=self.ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_complete=self._handle_complete,
            on_state_change=self._set_action_state,
        )

    def compose(self) -> ComposeResult:
        yield Static("Auth Tokens", classes="section-title")
        yield Static("Issue service-account refresh tokens.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Static("Account", classes="wizard-control-label")
            yield Input(id="auth-account")
            yield Static("Scopes", classes="wizard-control-label")
            yield Input(id="auth-scopes", placeholder="comma-separated scopes")
            yield Button("Issue Token", id="auth-issue", variant="primary")
        with Horizontal(classes="ops-actions"):
            yield Static("Tenant", classes="wizard-control-label")
            yield Input(id="auth-tenant")
            yield Static("Lifetime (min)", classes="wizard-control-label")
            yield Input(id="auth-lifetime")
            yield Static("Fingerprint", classes="wizard-control-label")
            yield Input(id="auth-fingerprint")
            yield Static("Force", classes="wizard-control-label")
            yield Switch(value=False, id="auth-force")
        with Horizontal(classes="ops-actions"):
            yield Static("Output", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("JSON", id="auth-output-json"),
                RadioButton("Text", id="auth-output-text"),
                RadioButton("Env", id="auth-output-env"),
                id="auth-output",
            )
            yield Static("Base URL", classes="wizard-control-label")
            yield Input(id="auth-base-url")
        yield Static("", id="auth-status", classes="section-footnote")
        yield Static("", id="auth-output-log", classes="ops-output")

    def on_mount(self) -> None:
        self.query_one("#auth-base-url", Input).value = resolve_base_url()
        try:
            output_format = resolve_output_format()
        except CLIError as exc:
            output_format = "json"
            self._set_status(str(exc))
        if output_format == "text":
            self.query_one("#auth-output-text", RadioButton).value = True
        elif output_format == "env":
            self.query_one("#auth-output-env", RadioButton).value = True
        else:
            self.query_one("#auth-output-json", RadioButton).value = True
        self.set_interval(0.4, self._runner.refresh_output)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "auth-issue":
            self._issue_token()

    def _issue_token(self) -> None:
        account = self.query_one("#auth-account", Input).value.strip()
        scopes_raw = self.query_one("#auth-scopes", Input).value.strip()
        if not account or not scopes_raw:
            self._set_status("Account and scopes are required.")
            return
        tenant = self.query_one("#auth-tenant", Input).value.strip() or None
        lifetime_raw = self.query_one("#auth-lifetime", Input).value.strip()
        fingerprint = self.query_one("#auth-fingerprint", Input).value.strip() or None
        force = self.query_one("#auth-force", Switch).value
        base_url_input = self.query_one("#auth-base-url", Input).value.strip()
        base_url = base_url_input or resolve_base_url()
        output_format = self._selected_output_format()

        lifetime_minutes: int | None = None
        if lifetime_raw:
            try:
                lifetime_minutes = int(lifetime_raw)
            except ValueError:
                self._set_status("Lifetime must be an integer number of minutes.")
                return

        try:
            scopes = parse_scopes(scopes_raw)
        except CLIError as exc:
            self._set_status(str(exc))
            return

        def _runner(ctx: CLIContext) -> str:
            request = IssueServiceAccountRequest(
                account=account,
                scopes=scopes,
                tenant_id=tenant,
                lifetime_minutes=lifetime_minutes,
                fingerprint=fingerprint,
                force=force,
            )
            response = issue_service_account(
                base_url=base_url,
                ctx=ctx,
                request=request,
            )
            return render_issue_output(response, output_format)

        if not self._runner.start("Issue token", _runner):
            self._set_status("Issuance already running.")

    def _handle_complete(self, result: ActionResult[str]) -> None:
        if result.error is None and result.value:
            self._set_output(result.value)

    def _selected_output_format(self) -> str:
        radio = self.query_one("#auth-output", RadioSet)
        selected = radio.pressed_button
        if selected is None or selected.id is None:
            return "json"
        if selected.id.endswith("text"):
            return "text"
        if selected.id.endswith("env"):
            return "env"
        return "json"

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#auth-issue", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#auth-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#auth-output-log", Static).update(message)


__all__ = ["AuthTokensPane"]
