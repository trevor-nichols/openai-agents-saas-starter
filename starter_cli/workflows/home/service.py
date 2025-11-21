from __future__ import annotations

from dataclasses import dataclass

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext
from starter_cli.core.status_models import ActionShortcut, ProbeResult, ServiceStatus
from starter_cli.ui import StarterTUI
from starter_cli.workflows.home.doctor import DoctorRunner


@dataclass(slots=True)
class HomeSummary:
    """Minimal summary used when the TUI is disabled."""

    probes: tuple[ProbeResult, ...] = ()
    services: tuple[ServiceStatus, ...] = ()


class HomeController:
    """Controller for the home hub."""

    def __init__(self, ctx: CLIContext) -> None:
        self.ctx = ctx

    def run(self, use_tui: bool = True) -> int:
        if not use_tui:
            runner = DoctorRunner(self.ctx, profile=self._detect_profile(), strict=False)
            probes, services, _summary = runner.collect()
            self._print_summary(HomeSummary(probes=tuple(probes), services=tuple(services)))
            return 0

        try:
            StarterTUI(self.ctx, initial_screen="home").run()
            return 0
        except KeyboardInterrupt:
            console.warn("Interrupted. Goodbye!", topic="home")
            return 130

    def _print_summary(self, summary: HomeSummary) -> None:
        console.rule("Starter CLI Home")
        console.info("Probes:")
        for probe in summary.probes:
            console.info(f"- {probe.name}: {probe.state.value} ({probe.detail or 'pending'})")
        console.info("Services:")
        for service in summary.services:
            console.info(
                f"- {service.label}: {service.state.value} ({service.detail or 'pending'})"
            )

    # legacy shortcut builder retained for compatibility with status models
    def _build_shortcuts(self, runner: DoctorRunner) -> list[ActionShortcut]:
        return [
            ActionShortcut(key="H", label="Home", description="Go to home"),
            ActionShortcut(key="S", label="Setup hub", description="Open setup menu"),
            ActionShortcut(key="R", label="Rerun probes", description="Refresh status"),
            ActionShortcut(key="G", label="Start dev", description="Run start dev"),
            ActionShortcut(key="D", label="Doctor --strict", description="Run doctor strict"),
            ActionShortcut(key="O", label="Open reports", description="Open var/reports"),
            ActionShortcut(key="Q", label="Quit", description="Exit dashboard"),
        ]

    def _detect_profile(self) -> str:
        try:
            from starter_cli.workflows.home.doctor import detect_profile

            return detect_profile()
        except Exception:
            return "local"


__all__ = ["HomeController", "HomeSummary"]
