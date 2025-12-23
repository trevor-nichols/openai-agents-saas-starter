from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from starter_contracts.provider_validation import ProviderViolation, validate_providers

from starter_cli.core import CLIContext
from starter_cli.core.status_models import ProbeResult, ServiceStatus
from starter_cli.services import ops_models
from starter_cli.services.infra import DependencyStatus, collect_dependency_statuses
from starter_cli.services.stripe_status import StripeStatus, load_stripe_status
from starter_cli.workflows.home.doctor import DoctorRunner, detect_profile
from starter_cli.workflows.setup_menu.detection import STALE_AFTER_DAYS, collect_setup_items
from starter_cli.workflows.setup_menu.models import SetupItem


@dataclass(frozen=True, slots=True)
class HomeSnapshot:
    probes: tuple[ProbeResult, ...]
    services: tuple[ServiceStatus, ...]
    summary: dict[str, int]
    profile: str
    strict: bool
    stack_state: str | None


@dataclass(frozen=True, slots=True)
class SetupSnapshot:
    items: tuple[SetupItem, ...]
    stale_window: timedelta


@dataclass(frozen=True, slots=True)
class LogsSnapshot:
    log_root: Path
    log_dir: Path
    entries: tuple[ops_models.LogEntry, ...]


@dataclass(frozen=True, slots=True)
class InfraSnapshot:
    dependencies: tuple[DependencyStatus, ...]


@dataclass(frozen=True, slots=True)
class ProvidersSnapshot:
    error: bool
    violations: tuple[ProviderViolation, ...]


@dataclass(frozen=True, slots=True)
class UsageSnapshot:
    summary: ops_models.UsageSummary | None


class HubService:
    """Aggregate data for the CLI hub panes."""

    def __init__(self, ctx: CLIContext) -> None:
        self.ctx = ctx

    def load_home(self, *, profile: str | None = None, strict: bool = False) -> HomeSnapshot:
        resolved_profile = profile or detect_profile()
        runner = DoctorRunner(self.ctx, profile=resolved_profile, strict=strict)
        probes, services, summary = runner.collect()
        stack_state = None
        stack_service = next((service for service in services if service.label == "stack"), None)
        if stack_service:
            raw_state = stack_service.metadata.get("state") if stack_service.metadata else None
            stack_state = raw_state if isinstance(raw_state, str) else stack_service.state.value
        return HomeSnapshot(
            probes=tuple(probes),
            services=tuple(services),
            summary=summary,
            profile=runner.profile,
            strict=runner.strict,
            stack_state=stack_state,
        )

    def load_setup(self, *, stale_days: int = STALE_AFTER_DAYS) -> SetupSnapshot:
        window = timedelta(days=stale_days)
        items = tuple(collect_setup_items(self.ctx, stale_after=window))
        return SetupSnapshot(items=items, stale_window=window)

    def load_logs(self) -> LogsSnapshot:
        log_root = ops_models.resolve_log_root(self.ctx.project_root, os.environ)
        log_dir = ops_models.resolve_active_log_dir(log_root)
        entries = tuple(ops_models.collect_log_entries(log_dir))
        return LogsSnapshot(log_root=log_root, log_dir=log_dir, entries=entries)

    def load_infra(self) -> InfraSnapshot:
        dependencies = tuple(collect_dependency_statuses())
        return InfraSnapshot(dependencies=dependencies)

    def load_providers(self) -> ProvidersSnapshot:
        settings = self.ctx.optional_settings()
        if settings is None:
            return ProvidersSnapshot(error=True, violations=())
        strict = False
        enforce = getattr(settings, "should_enforce_secret_overrides", None)
        if callable(enforce):
            strict = bool(enforce())
        violations = tuple(validate_providers(settings, strict=strict))
        return ProvidersSnapshot(error=False, violations=violations)

    def load_stripe(self) -> StripeStatus:
        return load_stripe_status(self.ctx)

    def load_usage(self) -> UsageSnapshot:
        reports_dir = self.ctx.project_root / "var" / "reports"
        report_path = reports_dir / "usage-dashboard.json"
        summary = ops_models.load_usage_summary(report_path)
        return UsageSnapshot(summary=summary)


__all__ = [
    "HomeSnapshot",
    "SetupSnapshot",
    "LogsSnapshot",
    "InfraSnapshot",
    "ProvidersSnapshot",
    "UsageSnapshot",
    "HubService",
]
