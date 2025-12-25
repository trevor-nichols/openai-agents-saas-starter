from __future__ import annotations

import json

from starter_contracts.keys import load_keyset
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

from starter_cli.core import CLIContext
from starter_cli.services.auth.security import configure_key_storage_secret_manager
from starter_cli.ui.action_runner import ActionResult, ActionRunner


class JwksPane(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="jwks", classes="section-pane")
        self.ctx = ctx
        self._runner = ActionRunner(
            ctx=self.ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_complete=self._handle_complete,
            on_state_change=self._set_action_state,
        )

    def compose(self) -> ComposeResult:
        yield Static("JWKS", classes="section-title")
        yield Static("Inspect current JSON Web Key Sets.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Button("Print JWKS", id="jwks-print", variant="primary")
        yield Static("", id="jwks-status", classes="section-footnote")
        yield Static("", id="jwks-output", classes="ops-output")

    def on_mount(self) -> None:
        self.set_interval(0.4, self._runner.refresh_output)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "jwks-print":
            self._run_print()

    def _run_print(self) -> None:
        def _runner(ctx: CLIContext) -> str:
            settings = ctx.require_settings()
            configure_key_storage_secret_manager(ctx)
            keyset = load_keyset(settings)
            document = keyset.materialize_jwks()
            return json.dumps(document.payload, indent=2)

        if not self._runner.start("Print JWKS", _runner):
            self._set_status("JWKS request already running.")

    def _handle_complete(self, result: ActionResult[str]) -> None:
        if result.error is None and result.value:
            self._set_output(result.value)

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#jwks-print", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#jwks-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#jwks-output", Static).update(message)


__all__ = ["JwksPane"]
