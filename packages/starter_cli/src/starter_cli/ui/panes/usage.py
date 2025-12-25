from __future__ import annotations

import argparse
import asyncio

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Collapsible, DataTable, Input, Static, Switch

from starter_cli.core import CLIContext
from starter_cli.services.usage.reporting import UsageWarning
from starter_cli.services.usage.usage_ops import (
    UsageExportConfig,
    UsageSyncConfig,
    export_usage_report,
    sync_usage_entitlements_with_config,
)
from starter_cli.ui.action_runner import ActionResult, ActionRunner
from starter_cli.workflows.home.hub import HubService


class UsagePane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="usage", classes="section-pane")
        self.ctx = ctx
        self.hub = hub
        self._runner = ActionRunner(
            ctx=self.ctx,
            on_status=self._set_status,
            on_output=self._set_output,
            on_complete=self._handle_complete,
            on_state_change=self._set_action_state,
        )
        self._refresh_task: asyncio.Task[None] | None = None

    def compose(self) -> ComposeResult:
        yield Static("Usage", classes="section-title")
        yield Static("Usage reports and entitlement artifacts.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Button("Refresh", id="usage-refresh", variant="primary")
            yield Button("Export Report", id="usage-export")
            yield Button("Sync Entitlements", id="usage-sync")
        with Collapsible(title="Export report options", id="usage-export-options", collapsed=True):
            with Horizontal(classes="ops-actions"):
                yield Static("Period start", classes="wizard-control-label")
                yield Input(id="usage-period-start")
                yield Static("Period end", classes="wizard-control-label")
                yield Input(id="usage-period-end")
            with Horizontal(classes="ops-actions"):
                yield Static("Tenants", classes="wizard-control-label")
                yield Input(id="usage-tenant")
                yield Static("Plans", classes="wizard-control-label")
                yield Input(id="usage-plan")
                yield Static("Features", classes="wizard-control-label")
                yield Input(id="usage-feature")
            with Horizontal(classes="ops-actions"):
                yield Static("Warn threshold", classes="wizard-control-label")
                yield Input(id="usage-warn-threshold", value="0.8")
                yield Static("Include inactive", classes="wizard-control-label")
                yield Switch(value=False, id="usage-include-inactive")
            with Horizontal(classes="ops-actions"):
                yield Static("JSON output", classes="wizard-control-label")
                yield Input(id="usage-output-json", placeholder="var/reports/usage-dashboard.json")
                yield Static("CSV output", classes="wizard-control-label")
                yield Input(id="usage-output-csv", placeholder="var/reports/usage-dashboard.csv")
            with Horizontal(classes="ops-actions"):
                yield Static("Skip JSON", classes="wizard-control-label")
                yield Switch(value=False, id="usage-no-json")
                yield Static("Skip CSV", classes="wizard-control-label")
                yield Switch(value=False, id="usage-no-csv")
        with Collapsible(
            title="Sync entitlements options",
            id="usage-sync-options",
            collapsed=True,
        ):
            with Horizontal(classes="ops-actions"):
                yield Static("Artifact path", classes="wizard-control-label")
                yield Input(
                    id="usage-sync-path",
                    placeholder="var/reports/usage-entitlements.json",
                )
                yield Static("Plans", classes="wizard-control-label")
                yield Input(id="usage-sync-plan")
            with Horizontal(classes="ops-actions"):
                yield Static("Prune missing", classes="wizard-control-label")
                yield Switch(value=False, id="usage-prune-missing")
                yield Static("Dry run", classes="wizard-control-label")
                yield Switch(value=False, id="usage-dry-run")
                yield Static("Allow disabled artifact", classes="wizard-control-label")
                yield Switch(value=False, id="usage-allow-disabled")
        yield DataTable(id="usage-summary", zebra_stripes=True)
        yield DataTable(id="usage-warnings", zebra_stripes=True)
        yield Static("", id="usage-status", classes="section-footnote")
        yield Static("", id="usage-output", classes="ops-output")

    async def on_mount(self) -> None:
        self.set_interval(0.4, self._runner.refresh_output)
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "usage-refresh":
            await self.refresh_data()
        elif event.button.id == "usage-export":
            self._run_export()
        elif event.button.id == "usage-sync":
            self._run_sync()

    async def refresh_data(self) -> None:
        snapshot = await asyncio.to_thread(self.hub.load_usage)
        summary_table = self.query_one("#usage-summary", DataTable)
        summary_table.clear(columns=True)
        summary_table.add_columns("Metric", "Value")
        if snapshot.summary is None:
            summary_table.add_row("Report", "Not found")
            self._set_status("Run export to generate usage artifacts.")
            self._render_warnings([])
            return
        summary = snapshot.summary
        summary_table.add_row("Generated at", summary.generated_at or "unknown")
        summary_table.add_row("Tenants", str(summary.tenant_count))
        summary_table.add_row("Features", str(summary.feature_count))
        summary_table.add_row("Warnings", str(summary.warning_count))
        self._render_warnings(list(snapshot.warnings))
        self._set_status("Usage report loaded.")

    def _render_warnings(self, warnings: list[UsageWarning]) -> None:
        warnings_table = self.query_one("#usage-warnings", DataTable)
        warnings_table.clear(columns=True)
        warnings_table.add_columns("Tenant", "Feature", "Status")
        if not warnings:
            warnings_table.add_row("-", "-", "No warnings in report")
            return
        for warning in warnings:
            warnings_table.add_row(warning.tenant_slug, warning.feature_key, warning.status)

    def _run_export(self) -> None:
        args = argparse.Namespace(
            period_start=self._text_value("usage-period-start") or None,
            period_end=self._text_value("usage-period-end") or None,
            tenant=self._split_list("usage-tenant"),
            plan=self._split_list("usage-plan"),
            feature=self._split_list("usage-feature"),
            include_inactive=self.query_one("#usage-include-inactive", Switch).value,
            warn_threshold=self._float_value("usage-warn-threshold", default=0.8),
            output_json=self._text_value("usage-output-json") or None,
            output_csv=self._text_value("usage-output-csv") or None,
            no_json=self.query_one("#usage-no-json", Switch).value,
            no_csv=self.query_one("#usage-no-csv", Switch).value,
        )

        def _runner(ctx: CLIContext) -> int:
            config = UsageExportConfig(
                period_start=args.period_start,
                period_end=args.period_end,
                tenants=args.tenant,
                plans=args.plan,
                features=args.feature,
                include_inactive=args.include_inactive,
                warn_threshold=args.warn_threshold,
                output_json=args.output_json,
                output_csv=args.output_csv,
                no_json=args.no_json,
                no_csv=args.no_csv,
            )
            export_usage_report(ctx, config)
            return 0

        if not self._runner.start("Export report", _runner):
            self._set_status("Another usage action is running.")

    def _run_sync(self) -> None:
        args = argparse.Namespace(
            path=self._text_value("usage-sync-path") or None,
            plan=self._split_list("usage-sync-plan") or None,
            prune_missing=self.query_one("#usage-prune-missing", Switch).value,
            dry_run=self.query_one("#usage-dry-run", Switch).value,
            allow_disabled_artifact=self.query_one("#usage-allow-disabled", Switch).value,
        )

        def _runner(ctx: CLIContext) -> int:
            config = UsageSyncConfig(
                path=args.path,
                plans=args.plan,
                prune_missing=args.prune_missing,
                dry_run=args.dry_run,
                allow_disabled_artifact=args.allow_disabled_artifact,
            )
            asyncio.run(sync_usage_entitlements_with_config(ctx, config))
            return 0

        if not self._runner.start("Sync entitlements", _runner):
            self._set_status("Another usage action is running.")

    def _handle_complete(self, result: ActionResult[int]) -> None:
        if result.label == "Export report" and result.error is None:
            self._refresh_task = asyncio.create_task(self.refresh_data())

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#usage-export", Button).disabled = running
        self.query_one("#usage-sync", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#usage-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#usage-output", Static).update(message)

    def _text_value(self, input_id: str) -> str:
        return self.query_one(f"#{input_id}", Input).value.strip()

    def _split_list(self, input_id: str) -> list[str]:
        raw = self._text_value(input_id)
        if not raw:
            return []
        parts = [part.strip() for part in raw.replace(";", ",").split(",")]
        return [part for part in parts if part]

    def _float_value(self, input_id: str, *, default: float) -> float:
        raw = self._text_value(input_id)
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            self._set_status(f"Invalid value for {input_id}; using {default}.")
            return default


__all__ = ["UsagePane"]
