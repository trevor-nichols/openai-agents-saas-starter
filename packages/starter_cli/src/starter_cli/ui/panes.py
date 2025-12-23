from __future__ import annotations

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol, runtime_checkable

from starter_contracts.provider_validation import ProviderViolation
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from starter_cli.core import CLIContext
from starter_cli.core.status_models import ProbeResult, ServiceStatus
from starter_cli.services.infra import DependencyStatus
from starter_cli.services.ops_models import LogEntry, UsageSummary, mask_value
from starter_cli.services.stripe_status import REQUIRED_ENV_KEYS, StripeStatus
from starter_cli.workflows.home.hub import HubService
from starter_cli.workflows.setup_menu.detection import STALE_AFTER_DAYS
from starter_cli.workflows.setup_menu.models import SetupAction, SetupItem

from .sections import SectionSpec
from .view_models import format_summary, probe_rows, service_rows, setup_row
from .wizard_pane import WizardLaunchConfig, WizardPane


class PlaceholderPane(Vertical):
    def __init__(self, section: SectionSpec) -> None:
        super().__init__(id=section.key, classes="section-pane")
        self.section = section

    def compose(self) -> ComposeResult:
        yield Static(self.section.label, classes="section-title")
        yield Static(self.section.description, classes="section-description")
        yield Static(self.section.detail, classes="section-detail")
        yield Static("More coming soon in this phase.", classes="section-footnote")


class HomePane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="home", classes="section-pane")
        self.ctx = ctx
        self.hub = hub
        self._summary: dict[str, int] = {}
        self._probes: list[ProbeResult] = []
        self._services: list[ServiceStatus] = []
        self._profile: str = "local"
        self._strict: bool = False
        self._stack_state: str | None = None

    def compose(self) -> ComposeResult:
        yield Static("Home", classes="section-title")
        yield Static("", id="home-summary", classes="section-summary")
        with Horizontal(classes="home-actions"):
            yield Button("Refresh", id="home-refresh", variant="primary")
        with Horizontal(classes="home-tables"):
            yield DataTable(id="home-probes", zebra_stripes=True)
            yield DataTable(id="home-services", zebra_stripes=True)
        yield Static("", id="home-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "home-refresh":
            await self.refresh_data()

    async def refresh_data(self) -> None:
        self._set_status("Refreshing status...")
        await asyncio.to_thread(self._collect)
        self._render_summary()
        self._render_tables()
        self._set_status(self._timestamp_label())

    def _collect(self) -> None:
        snapshot = self.hub.load_home()
        self._probes = list(snapshot.probes)
        self._services = list(snapshot.services)
        self._summary = snapshot.summary
        self._profile = snapshot.profile
        self._strict = snapshot.strict
        self._stack_state = snapshot.stack_state

    def _render_summary(self) -> None:
        summary_text = format_summary(
            self._summary,
            profile=self._profile,
            strict=self._strict,
            stack_state=self._stack_state,
        )
        self.query_one("#home-summary", Static).update(summary_text)

    def _render_tables(self) -> None:
        probe_table = self.query_one("#home-probes", DataTable)
        probe_table.clear(columns=True)
        probe_table.add_columns("Probe", "Status", "Detail")
        for row in probe_rows(self._probes):
            probe_table.add_row(*row)

        service_table = self.query_one("#home-services", DataTable)
        service_table.clear(columns=True)
        service_table.add_columns("Service", "Status", "Detail")
        for row in service_rows(self._services):
            service_table.add_row(*row)

    def _set_status(self, message: str) -> None:
        self.query_one("#home-status", Static).update(message)

    def _timestamp_label(self) -> str:
        now = datetime.now(UTC).astimezone()
        return f"Updated {now.strftime('%H:%M:%S')}"


class SetupPane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService, *, stale_days: int) -> None:
        super().__init__(id="setup", classes="section-pane")
        self.ctx = ctx
        self.hub = hub
        self._items: list[SetupItem] = []
        self._stale_window = timedelta(days=stale_days)

    def compose(self) -> ComposeResult:
        yield Static("Setup Hub", classes="section-title")
        yield Static(
            "Guided setup actions for secrets, infra, and providers.",
            classes="section-description",
        )
        with Horizontal(classes="setup-actions"):
            yield Button("Refresh", id="setup-refresh", variant="primary")
            yield Button("Run Selected", id="setup-run")
        yield DataTable(id="setup-table", zebra_stripes=True)
        yield Static("", id="setup-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "setup-refresh":
            await self.refresh_data()
        elif event.button.id == "setup-run":
            await self._run_selected()

    async def refresh_data(self) -> None:
        self._set_status("Refreshing setup items...")
        await asyncio.to_thread(self._load_items)
        self._render_table()
        self._set_status("Select a row and choose Run Selected.")

    def _load_items(self) -> None:
        snapshot = self.hub.load_setup(stale_days=self._stale_window.days)
        self._items = list(snapshot.items)

    def _render_table(self) -> None:
        table = self.query_one("#setup-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Status", "Setup", "Detail", "Progress", "Last Run")
        for item in self._items:
            table.add_row(*setup_row(item), key=item.key)
        if table.row_count:
            table.focus()
            table.move_cursor(row=0, column=0)

    async def _run_selected(self) -> None:
        table = self.query_one("#setup-table", DataTable)
        if table.cursor_row is None:
            self._set_status("Choose a setup row first.")
            return
        if table.cursor_row < 0 or table.cursor_row >= len(self._items):
            self._set_status("Selection out of range.")
            return
        item = self._items[table.cursor_row]
        if not item.actions:
            self._set_status("No actions available for this setup item.")
            return
        await self._run_action(item.actions[0])
        await self.refresh_data()

    async def _run_action(self, action: SetupAction) -> None:
        if action.key == "secrets_onboard":
            if self._open_secrets_onboard():
                return
        if action.route:
            if self._navigate(action.route):
                self._set_status(f"Opened {action.label}.")
                return
        if action.command:
            self._set_status(f"Run: {' '.join(action.command)}")
            return
        self._set_status("No action available for this item.")

    def _set_status(self, message: str) -> None:
        self.query_one("#setup-status", Static).update(message)

    def _navigate(self, route: str) -> bool:
        app = self.app
        if isinstance(app, _Navigator):
            app.action_go(route)
            return True
        return False

    def _open_secrets_onboard(self) -> bool:
        app = self.app
        if isinstance(app, _SecretsLauncher):
            app.open_secrets_onboard()
            return True
        return False


@runtime_checkable
class _Navigator(Protocol):
    def action_go(self, section_key: str) -> None: ...


@runtime_checkable
class _SecretsLauncher(Protocol):
    def open_secrets_onboard(self) -> None: ...


async def _run_command(
    output: Static,
    *,
    command: list[str],
    cwd: Path,
    label: str,
) -> None:
    output.update(f"Running {label}...")
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        text = stdout.decode(errors="ignore").strip() if stdout else ""
        if not text:
            text = f"{label} exited with {proc.returncode}"
        else:
            text = f"{label} exited with {proc.returncode}\n{text}"
        output.update(text)
    except FileNotFoundError as exc:
        output.update(f"Command not found: {exc}")
    except Exception as exc:  # pragma: no cover - defensive
        output.update(f"Command failed: {exc}")


@dataclass(frozen=True, slots=True)
class ProvidersLoadResult:
    error: bool
    violations: list[ProviderViolation]


@dataclass(frozen=True, slots=True)
class StripeLoadResult:
    values: dict[str, str | None]
    enable_billing: str


@dataclass(frozen=True, slots=True)
class UsageLoadResult:
    summary: UsageSummary | None


class LogsPane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="logs", classes="section-pane")
        self.ctx = ctx
        self.hub = hub
        self._log_root: Path | None = None
        self._log_dir: Path | None = None
        self._entries: list[LogEntry] = []

    def compose(self) -> ComposeResult:
        yield Static("Logs", classes="section-title")
        yield Static("", id="logs-summary", classes="section-summary")
        with Horizontal(classes="ops-actions"):
            yield Button("Refresh", id="logs-refresh", variant="primary")
            yield Button("Tail API", id="logs-tail-api")
            yield Button("Tail API Errors", id="logs-tail-errors")
            yield Button("Tail CLI", id="logs-tail-cli")
        yield DataTable(id="logs-table", zebra_stripes=True)
        yield Static("", id="logs-status", classes="section-footnote")
        yield Static("", id="logs-output", classes="ops-output")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "logs-refresh":
            await self.refresh_data()
        elif event.button.id == "logs-tail-api":
            await self._tail_entry("api/all.log")
        elif event.button.id == "logs-tail-errors":
            await self._tail_entry("api/error.log")
        elif event.button.id == "logs-tail-cli":
            await self._tail_entry("cli/*.log")

    async def refresh_data(self) -> None:
        await asyncio.to_thread(self._collect)
        self._render_table()

    def _collect(self) -> None:
        snapshot = self.hub.load_logs()
        self._log_root = snapshot.log_root
        self._log_dir = snapshot.log_dir
        self._entries = list(snapshot.entries)

    def _render_table(self) -> None:
        table = self.query_one("#logs-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Target", "Path", "Status")
        for entry in self._entries:
            status = "present" if entry.exists else "missing"
            table.add_row(entry.name, str(entry.path), status)
        summary = f"Log root: {self._log_root} | Active dir: {self._log_dir}"
        self.query_one("#logs-summary", Static).update(summary)
        self.query_one("#logs-status", Static).update("Select a Tail action to preview logs.")

    async def _tail_entry(self, name: str) -> None:
        entry = next((item for item in self._entries if item.name == name), None)
        if entry is None:
            self.query_one("#logs-status", Static).update(f"No log entry named {name}.")
            return
        target = entry.path
        if target.is_dir():
            candidates = sorted(
                target.glob("*.log"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            if not candidates:
                self.query_one("#logs-status", Static).update("No CLI log files found.")
                return
            target = candidates[0]
        if not target.exists():
            self.query_one("#logs-status", Static).update(f"Missing log file: {target}")
            return
        await _run_command(
            self.query_one("#logs-output", Static),
            command=["tail", "-n", "200", str(target)],
            cwd=self.ctx.project_root,
            label=f"tail {name}",
        )


class InfraPane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="infra", classes="section-pane")
        self.ctx = ctx
        self.hub = hub
        self._deps: list[DependencyStatus] = []

    def compose(self) -> ComposeResult:
        yield Static("Infra", classes="section-title")
        yield Static("Local tooling and compose helpers.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Button("Refresh", id="infra-refresh", variant="primary")
            yield Button("Compose Up", id="infra-compose-up")
            yield Button("Compose Down", id="infra-compose-down")
            yield Button("Vault Up", id="infra-vault-up")
            yield Button("Vault Down", id="infra-vault-down")
        yield DataTable(id="infra-deps", zebra_stripes=True)
        yield Static("", id="infra-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "infra-refresh":
            await self.refresh_data()
        elif event.button.id == "infra-compose-up":
            await self._run_just("dev-up")
        elif event.button.id == "infra-compose-down":
            await self._run_just("dev-down")
        elif event.button.id == "infra-vault-up":
            await self._run_just("vault-up")
        elif event.button.id == "infra-vault-down":
            await self._run_just("vault-down")

    async def refresh_data(self) -> None:
        self.query_one("#infra-status", Static).update("Refreshing dependency status...")
        snapshot = await asyncio.to_thread(self.hub.load_infra)
        self._deps = list(snapshot.dependencies)
        table = self.query_one("#infra-deps", DataTable)
        table.clear(columns=True)
        table.add_columns("Dependency", "Status", "Version", "Path", "Hint")
        for dep in self._deps:
            table.add_row(
                dep.name,
                dep.status,
                dep.version or "",
                dep.path or "",
                "" if dep.status == "ok" else dep.hint,
            )
        self.query_one("#infra-status", Static).update("Dependency check complete.")

    async def _run_just(self, target: str) -> None:
        await _run_command(
            self.query_one("#infra-status", Static),
            command=["just", target],
            cwd=self.ctx.project_root,
            label=f"just {target}",
        )


class ProvidersPane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="providers", classes="section-pane")
        self.ctx = ctx
        self.hub = hub

    def compose(self) -> ComposeResult:
        yield Static("Providers", classes="section-title")
        yield Static("Validate provider configuration status.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Button("Refresh", id="providers-refresh", variant="primary")
        yield DataTable(id="providers-table", zebra_stripes=True)
        yield Static("", id="providers-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "providers-refresh":
            await self.refresh_data()

    async def refresh_data(self) -> None:
        self.query_one("#providers-status", Static).update("Validating providers...")
        result = await asyncio.to_thread(self._load)
        table = self.query_one("#providers-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Provider", "Severity", "Message")
        if result.error:
            table.add_row("settings", "error", "Settings unavailable; load env files first.")
            self.query_one("#providers-status", Static).update("Unable to load settings.")
            return
        violations = result.violations
        if not violations:
            table.add_row("all", "ok", "All providers are configured.")
            self.query_one("#providers-status", Static).update("Provider validation passed.")
            return
        for violation in violations:
            severity = "fatal" if violation.fatal else "warn"
            table.add_row(violation.provider, severity, violation.message)
        self.query_one("#providers-status", Static).update(
            "Provider validation finished with findings."
        )

    def _load(self) -> ProvidersLoadResult:
        snapshot = self.hub.load_providers()
        return ProvidersLoadResult(error=snapshot.error, violations=list(snapshot.violations))


class StripePane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="stripe", classes="section-pane")
        self.ctx = ctx
        self.hub = hub
        self._env_values: dict[str, str | None] = {}

    def compose(self) -> ComposeResult:
        yield Static("Stripe", classes="section-title")
        yield Static("Stripe billing configuration overview.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Button("Refresh", id="stripe-refresh", variant="primary")
            yield Button("Show Setup Command", id="stripe-setup")
            yield Button("Show Webhook Command", id="stripe-webhook")
        yield DataTable(id="stripe-table", zebra_stripes=True)
        yield Static("", id="stripe-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "stripe-refresh":
            await self.refresh_data()
        elif event.button.id == "stripe-setup":
            self.query_one("#stripe-status", Static).update(
                "Run: starter-cli stripe setup"
            )
        elif event.button.id == "stripe-webhook":
            self.query_one("#stripe-status", Static).update(
                "Run: starter-cli stripe webhook-secret"
            )

    async def refresh_data(self) -> None:
        data = await asyncio.to_thread(self._load)
        self._env_values = data.values
        table = self.query_one("#stripe-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Key", "Status", "Value")
        for key in REQUIRED_ENV_KEYS:
            value = self._env_values.get(key)
            status = "set" if value else "missing"
            display = mask_value(value)
            if key == "STRIPE_PRODUCT_PRICE_MAP" and value:
                display = "configured"
            table.add_row(key, status, display)
        enable_billing = data.enable_billing
        if enable_billing:
            table.add_row("ENABLE_BILLING", "set", enable_billing)
        self.query_one("#stripe-status", Static).update("Stripe status loaded.")

    def _load(self) -> StripeLoadResult:
        snapshot: StripeStatus = self.hub.load_stripe()
        return StripeLoadResult(values=snapshot.values, enable_billing=snapshot.enable_billing)


class UsagePane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="usage", classes="section-pane")
        self.ctx = ctx
        self.hub = hub

    def compose(self) -> ComposeResult:
        yield Static("Usage", classes="section-title")
        yield Static("Usage reports and entitlement artifacts.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Button("Refresh", id="usage-refresh", variant="primary")
        yield DataTable(id="usage-summary", zebra_stripes=True)
        yield DataTable(id="usage-warnings", zebra_stripes=True)
        yield Static("", id="usage-status", classes="section-footnote")

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "usage-refresh":
            await self.refresh_data()

    async def refresh_data(self) -> None:
        data = await asyncio.to_thread(self._load)
        reports_dir = self.ctx.project_root / "var" / "reports"
        report_path = reports_dir / "usage-dashboard.json"
        summary_table = self.query_one("#usage-summary", DataTable)
        summary_table.clear(columns=True)
        summary_table.add_columns("Metric", "Value")
        if data.summary is None:
            summary_table.add_row("Report", "Not found")
            self.query_one("#usage-status", Static).update(
                "Run `starter-cli usage export-report` to generate artifacts."
            )
            return
        summary = data.summary
        summary_table.add_row("Generated at", summary.generated_at or "unknown")
        summary_table.add_row("Tenants", str(summary.tenant_count))
        summary_table.add_row("Features", str(summary.feature_count))
        summary_table.add_row("Warnings", str(summary.warning_count))
        self._render_warnings(report_path)
        self.query_one("#usage-status", Static).update("Usage report loaded.")

    def _load(self) -> UsageLoadResult:
        snapshot = self.hub.load_usage()
        return UsageLoadResult(summary=snapshot.summary)

    def _render_warnings(self, report_path: Path) -> None:
        warnings_table = self.query_one("#usage-warnings", DataTable)
        warnings_table.clear(columns=True)
        warnings_table.add_columns("Tenant", "Feature", "Status")
        warning_rows = _collect_usage_warnings(report_path, limit=5)
        if not warning_rows:
            warnings_table.add_row("-", "-", "No warnings in report")
            return
        for row in warning_rows:
            warnings_table.add_row(*row)


def _collect_usage_warnings(path: Path, *, limit: int) -> list[tuple[str, str, str]]:
    if not path.exists():
        return []
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return []
    import json

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    rows: list[tuple[str, str, str]] = []
    for tenant in data.get("tenants", []):
        slug = tenant.get("tenant_slug") or "unknown"
        for feature in tenant.get("features", []):
            status = feature.get("status")
            if status not in {"approaching", "soft_limit_exceeded", "hard_limit_exceeded"}:
                continue
            rows.append((slug, feature.get("feature_key", ""), status))
            if len(rows) >= limit:
                return rows
    return rows


def build_panes(
    ctx: CLIContext,
    sections: Iterable[SectionSpec],
    *,
    hub: HubService,
    wizard_config: WizardLaunchConfig | None = None,
):
    panes: list[Vertical] = []
    for section in sections:
        if section.key == "home":
            panes.append(HomePane(ctx, hub))
        elif section.key == "setup":
            panes.append(SetupPane(ctx, hub, stale_days=STALE_AFTER_DAYS))
        elif section.key == "wizard":
            panes.append(WizardPane(ctx, config=wizard_config))
        elif section.key == "logs":
            panes.append(LogsPane(ctx, hub))
        elif section.key == "infra":
            panes.append(InfraPane(ctx, hub))
        elif section.key == "providers":
            panes.append(ProvidersPane(ctx, hub))
        elif section.key == "stripe":
            panes.append(StripePane(ctx, hub))
        elif section.key == "usage":
            panes.append(UsagePane(ctx, hub))
        else:
            panes.append(PlaceholderPane(section))
    return panes


__all__ = [
    "HomePane",
    "SetupPane",
    "LogsPane",
    "InfraPane",
    "ProvidersPane",
    "StripePane",
    "UsagePane",
    "PlaceholderPane",
    "build_panes",
]
