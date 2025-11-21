from __future__ import annotations

import time
from dataclasses import dataclass

from rich.live import Live

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext
from starter_cli.core.status_models import ActionShortcut, ProbeResult, ServiceStatus
from starter_cli.workflows.home.doctor import DoctorRunner, detect_profile
from starter_cli.workflows.home.ui.layout import build_home_layout


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
        runner = DoctorRunner(self.ctx, profile=detect_profile(), strict=False)
        try:
            probes, services, summary = runner.collect(log_suppressed=True)
        except TypeError:
            probes, services, summary = runner.collect()
        try:
            if use_tui:
                self._render_tui(runner, probes, services, summary)
            else:
                self._print_summary(HomeSummary(probes=tuple(probes), services=tuple(services)))
        except KeyboardInterrupt:
            console.warn("Interrupted. Goodbye!", topic="home")
            return 130  # conventional exit code for SIGINT
        return 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _render_tui(
        self,
        runner: DoctorRunner,
        probes: list[ProbeResult],
        services: list[ServiceStatus],
        summary: dict[str, int],
    ) -> None:
        shortcuts = self._build_shortcuts(runner)
        refresh_seconds = 2.0
        refresh_hz = 1 / refresh_seconds
        layout = build_home_layout(
            probes=probes,
            services=services,
            summary=summary,
            profile=runner.profile,
            strict=runner.strict,
            shortcuts=shortcuts,
        )

        try:
            with Live(
                layout,
                refresh_per_second=refresh_hz,
                console=console._rich_out,
            ) as live:
                while True:
                    runner = DoctorRunner(self.ctx, profile=detect_profile(), strict=False)
                    try:
                        probes, services, summary = runner.collect(log_suppressed=False)
                    except TypeError:
                        probes, services, summary = runner.collect()
                    live.update(
                        build_home_layout(
                            probes=probes,
                            services=services,
                            summary=summary,
                            profile=runner.profile,
                            strict=runner.strict,
                            shortcuts=shortcuts,
                        )
                    )
                    time.sleep(refresh_seconds)
        except KeyboardInterrupt:
            console.note("Closing home dashboard…", topic="home")
        except Exception as exc:  # pragma: no cover - defensive guard
            console.error(f"Home dashboard error: {exc}; showing summary instead.", topic="home")
            self._print_summary(HomeSummary(probes=tuple(probes), services=tuple(services)))

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

    def _build_shortcuts(self, runner: DoctorRunner) -> list[ActionShortcut]:
        # Placeholders; callbacks are stubs to keep TUI view-only for now
        return [
            ActionShortcut(key="R", label="Rerun probes", description="Refresh status"),
            ActionShortcut(key="S", label="Start dev", description="Run start dev"),
            ActionShortcut(key="D", label="Doctor --strict", description="Run doctor strict"),
            ActionShortcut(key="O", label="Open reports", description="Open var/reports"),
        ]


__all__ = ["HomeController", "HomeSummary"]
