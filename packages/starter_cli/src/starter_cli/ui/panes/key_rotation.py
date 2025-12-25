from __future__ import annotations

import json

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Static

from starter_cli.core import CLIContext
from starter_cli.services.auth.security import rotate_signing_keys
from starter_cli.ui.action_runner import ActionResult, ActionRunner


class KeyRotationPane(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="key-rotation", classes="section-pane")
        self.ctx = ctx
        self._runner = ActionRunner(
            ctx=self.ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_complete=self._handle_complete,
            on_state_change=self._set_action_state,
        )

    def compose(self) -> ComposeResult:
        yield Static("Key Rotation", classes="section-title")
        yield Static("Rotate Ed25519 signing keys.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Static("KID", classes="wizard-control-label")
            yield Input(id="key-rotation-kid")
            yield Button("Rotate", id="key-rotation-run", variant="primary")
        yield Static("", id="key-rotation-status", classes="section-footnote")
        yield Static("", id="key-rotation-output", classes="ops-output")

    def on_mount(self) -> None:
        self.set_interval(0.4, self._runner.refresh_output)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "key-rotation-run":
            self._run_rotation()

    def _run_rotation(self) -> None:
        kid = self.query_one("#key-rotation-kid", Input).value.strip() or None

        def _runner(ctx: CLIContext) -> str:
            result = rotate_signing_keys(ctx, kid=kid)
            return json.dumps(result.to_dict(), indent=2)

        if not self._runner.start("Rotate keys", _runner):
            self._set_status("Rotation already running.")

    def _handle_complete(self, result: ActionResult[str]) -> None:
        if result.error is None and result.value:
            self._set_output(result.value)

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#key-rotation-run", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#key-rotation-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#key-rotation-output", Static).update(message)


__all__ = ["KeyRotationPane"]
