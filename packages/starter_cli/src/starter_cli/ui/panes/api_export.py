from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Static, Switch

from starter_cli.core import CLIContext
from starter_cli.services.api.export import OpenApiExportConfig, OpenAPIExporter
from starter_cli.ui.action_runner import ActionRunner


class ApiExportPane(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="api-export", classes="section-pane")
        self.ctx = ctx
        self._runner: ActionRunner[int] = ActionRunner(
            ctx=self.ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_state_change=self._set_action_state,
        )

    def compose(self) -> ComposeResult:
        yield Static("API Export", classes="section-title")
        yield Static("Export OpenAPI schema artifacts.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Static("Output path", classes="wizard-control-label")
            yield Input(id="api-output", value="apps/api-service/.artifacts/openapi.json")
            yield Button("Export", id="api-export", variant="primary")
        with Horizontal(classes="ops-actions"):
            yield Static("Enable billing", classes="wizard-control-label")
            yield Switch(value=False, id="api-enable-billing")
            yield Static("Enable fixtures", classes="wizard-control-label")
            yield Switch(value=False, id="api-enable-fixtures")
            yield Static("Title", classes="wizard-control-label")
            yield Input(id="api-title")
            yield Static("Version", classes="wizard-control-label")
            yield Input(id="api-version")
        yield Static("", id="api-status", classes="section-footnote")
        yield Static("", id="api-output-log", classes="ops-output")

    def on_mount(self) -> None:
        self.set_interval(0.4, self._runner.refresh_output)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "api-export":
            self._run_export()

    def _run_export(self) -> None:
        output = self.query_one("#api-output", Input).value.strip()
        enable_billing = self.query_one("#api-enable-billing", Switch).value
        enable_fixtures = self.query_one("#api-enable-fixtures", Switch).value
        title = self.query_one("#api-title", Input).value.strip() or None
        version = self.query_one("#api-version", Input).value.strip() or None

        def _runner(ctx: CLIContext) -> int:
            config = OpenApiExportConfig(
                output=output,
                enable_billing=enable_billing,
                enable_test_fixtures=enable_fixtures,
                title=title,
                version=version,
            )
            exporter = OpenAPIExporter(ctx=ctx, config=config)
            exporter.run()
            return 0

        if not self._runner.start("Export OpenAPI", _runner):
            self._set_status("Export already running.")

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#api-export", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#api-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#api-output-log", Static).update(message)


__all__ = ["ApiExportPane"]
