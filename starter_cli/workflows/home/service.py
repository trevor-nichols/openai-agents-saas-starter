from __future__ import annotations

from dataclasses import dataclass

from rich.live import Live

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext
from starter_cli.core.status_models import ProbeResult, ProbeState, ServiceStatus
from starter_cli.workflows.home.doctor import DoctorRunner, detect_profile
from starter_cli.workflows.home.ui.layout import build_home_layout


@dataclass(slots=True)
class HomeSummary:
    """Minimal summary used when the TUI is disabled."""

    probes: tuple[ProbeResult, ...] = ()
    services: tuple[ServiceStatus, ...] = ()


class HomeController:
    """Placeholder controller for the upcoming home hub.

    The initial implementation keeps the contract stable while the actual UI and
    probe plumbing are built. Once probes and the TUI land, this controller will
    assemble results and render them through Rich/Textual.
    """

    def __init__(self, ctx: CLIContext) -> None:
        self.ctx = ctx

    def run(self, use_tui: bool = True) -> int:
        runner = DoctorRunner(self.ctx, profile=detect_profile(), strict=False)
        probes, services, summary = runner.collect()
        if use_tui:
            layout = build_home_layout(
                probes=probes,
                services=services,
                summary=summary,
                profile=runner.profile,
                strict=runner.strict,
            )
            with Live(layout, refresh_per_second=2, console=console._rich_out):
                # Static rendering for now; future revisions may stream updates.
                pass
        else:
            self._print_summary(HomeSummary(probes=tuple(probes), services=tuple(services)))
        return 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
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


__all__ = ["HomeController", "HomeSummary"]
