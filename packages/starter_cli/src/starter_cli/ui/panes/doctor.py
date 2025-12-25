from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, RadioButton, RadioSet, Static, Switch

from starter_cli.core import CLIContext
from starter_cli.core.status_models import ProbeResult, ServiceStatus
from starter_cli.ui.action_runner import ActionResult, ActionRunner
from starter_cli.ui.view_models import probe_rows, service_rows
from starter_cli.workflows.home.doctor import DoctorRunner, detect_profile


@dataclass(slots=True)
class DoctorRunResult:
    probes: list[ProbeResult]
    services: list[ServiceStatus]
    summary: dict[str, int]
    json_path: Path
    markdown_path: Path


class DoctorPane(Vertical):
    def __init__(self, ctx: CLIContext) -> None:
        super().__init__(id="doctor", classes="section-pane")
        self.ctx = ctx
        self._runner = ActionRunner(
            ctx=self.ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_complete=self._handle_complete,
            on_state_change=self._set_action_state,
        )

    def compose(self) -> ComposeResult:
        yield Static("Doctor", classes="section-title")
        yield Static("Run readiness checks and export reports.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Static("Profile", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Auto", id="doctor-profile-auto"),
                RadioButton("Demo", id="doctor-profile-demo"),
                RadioButton("Staging", id="doctor-profile-staging"),
                RadioButton("Production", id="doctor-profile-production"),
                id="doctor-profile",
            )
            yield Static("Strict", classes="wizard-control-label")
            yield Switch(value=False, id="doctor-strict")
            yield Button("Run Doctor", id="doctor-run", variant="primary")
        with Horizontal(classes="ops-actions"):
            yield Static("Profile override", classes="wizard-control-label")
            yield Input(id="doctor-profile-override")
            yield Static("JSON path", classes="wizard-control-label")
            yield Input(id="doctor-json-path")
            yield Static("Markdown path", classes="wizard-control-label")
            yield Input(id="doctor-markdown-path")
        yield Static("", id="doctor-summary", classes="section-summary")
        with Horizontal(classes="home-tables"):
            yield DataTable(id="doctor-probes", zebra_stripes=True)
            yield DataTable(id="doctor-services", zebra_stripes=True)
        yield Static("", id="doctor-status", classes="section-footnote")
        yield Static("", id="doctor-output", classes="ops-output")

    def on_mount(self) -> None:
        self.query_one("#doctor-profile-auto", RadioButton).value = True
        self.set_interval(0.4, self._runner.refresh_output)
        self._render_tables([], [])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "doctor-run":
            self._run_doctor()

    def _run_doctor(self) -> None:
        profile = self._resolve_profile()
        strict = self.query_one("#doctor-strict", Switch).value
        json_path = self._path_value("doctor-json-path")
        markdown_path = self._path_value("doctor-markdown-path")

        def _runner(ctx: CLIContext) -> DoctorRunResult:
            runner = DoctorRunner(ctx, profile=profile, strict=strict)
            probes, services, summary = runner.collect()
            ctx.console.info(
                f"Doctor summary: ok={summary.get('ok',0)} warn={summary.get('warn',0)} "
                f"error={summary.get('error',0)} skipped={summary.get('skipped',0)}",
                topic="doctor",
            )
            json_out, md_out = runner.write_reports(
                probes=probes,
                services=services,
                summary=summary,
                json_path=json_path,
                markdown_path=markdown_path,
            )
            return DoctorRunResult(
                probes=probes,
                services=services,
                summary=summary,
                json_path=json_out,
                markdown_path=md_out,
            )

        if not self._runner.start("Doctor", _runner):
            self._set_status("Doctor run already in progress.")

    def _handle_complete(self, result: ActionResult[DoctorRunResult]) -> None:
        if result.error or result.value is None:
            return
        run = result.value
        summary = run.summary
        summary_text = (
            f"Profile: {self._resolve_profile()} | Strict: "
            f"{'yes' if self.query_one('#doctor-strict', Switch).value else 'no'} | "
            f"ok={summary.get('ok',0)} warn={summary.get('warn',0)} "
            f"error={summary.get('error',0)} skipped={summary.get('skipped',0)}"
        )
        summary_text += f" | JSON: {run.json_path} | MD: {run.markdown_path}"
        self.query_one("#doctor-summary", Static).update(summary_text)
        self._render_tables(run.probes, run.services)

    def _render_tables(
        self,
        probes: list[ProbeResult],
        services: list[ServiceStatus],
    ) -> None:
        probe_table = self.query_one("#doctor-probes", DataTable)
        probe_table.clear(columns=True)
        probe_table.add_columns("Probe", "Status", "Detail")
        for row in probe_rows(probes):
            probe_table.add_row(*row)

        service_table = self.query_one("#doctor-services", DataTable)
        service_table.clear(columns=True)
        service_table.add_columns("Service", "Status", "Detail")
        for row in service_rows(services):
            service_table.add_row(*row)

    def _resolve_profile(self) -> str:
        override = self.query_one("#doctor-profile-override", Input).value.strip()
        if override:
            return override
        radio = self.query_one("#doctor-profile", RadioSet)
        selected = radio.pressed_button
        if selected is None or selected.id is None:
            return detect_profile()
        if selected.id.endswith("demo"):
            return "demo"
        if selected.id.endswith("staging"):
            return "staging"
        if selected.id.endswith("production"):
            return "production"
        return detect_profile()

    def _path_value(self, input_id: str) -> Path | None:
        raw = self.query_one(f"#{input_id}", Input).value.strip()
        if not raw:
            return None
        return Path(raw).expanduser().resolve()

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#doctor-run", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#doctor-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#doctor-output", Static).update(message)


__all__ = ["DoctorPane"]
