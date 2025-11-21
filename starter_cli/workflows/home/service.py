from __future__ import annotations

import queue
import subprocess
import threading
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
        stop_event = threading.Event()
        action_queue: queue.Queue[str] = queue.Queue()
        listener = threading.Thread(
            target=self._listen_for_shortcuts,
            args=(action_queue, stop_event, shortcuts),
            daemon=True,
        )
        listener.start()
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
                while not stop_event.is_set():
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
                    self._drain_actions(action_queue, stop_event)
                    time.sleep(refresh_seconds)
        except KeyboardInterrupt:
            console.note("Closing home dashboard…", topic="home")
        except Exception as exc:  # pragma: no cover - defensive guard
            console.error(f"Home dashboard error: {exc}; showing summary instead.", topic="home")
            self._print_summary(HomeSummary(probes=tuple(probes), services=tuple(services)))
        finally:
            stop_event.set()

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
            ActionShortcut(key="G", label="Start dev", description="Run start dev"),
            ActionShortcut(key="D", label="Doctor --strict", description="Run doctor strict"),
            ActionShortcut(key="S", label="Setup hub", description="Open setup menu"),
            ActionShortcut(key="O", label="Open reports", description="Open var/reports"),
            ActionShortcut(key="Q", label="Quit", description="Exit dashboard"),
        ]

    def _listen_for_shortcuts(
        self,
        action_queue: queue.Queue[str],
        stop_event: threading.Event,
        shortcuts: list[ActionShortcut],
    ) -> None:
        hint = "/".join(shortcut.key for shortcut in shortcuts)
        while not stop_event.is_set():
            try:
                choice = console.input(f"[cyan]Shortcut[/] ({hint}): ").strip()
            except (EOFError, KeyboardInterrupt):
                stop_event.set()
                break
            if not choice:
                continue
            action_queue.put(choice.upper())
            if choice.upper() == "Q":
                stop_event.set()

    def _drain_actions(self, action_queue: queue.Queue[str], stop_event: threading.Event) -> None:
        while not action_queue.empty():
            try:
                key = action_queue.get_nowait()
            except queue.Empty:
                return
            if key == "R":
                console.info("Refresh requested.", topic="home")
                continue
            if key == "Q":
                stop_event.set()
                break
            self._handle_action(key)

    def _handle_action(self, key: str) -> None:
        key = key.upper()
        if key == "G":
            self._spawn_command(
                ["python", "-m", "starter_cli.app", "start", "dev"],
                label="start dev",
            )
        elif key == "D":
            self._spawn_command(
                ["python", "-m", "starter_cli.app", "doctor", "--strict"],
                label="doctor --strict",
            )
        elif key == "S":
            self._spawn_command(
                ["python", "-m", "starter_cli.app", "setup", "menu"],
                label="setup menu",
            )
        elif key == "O":
            reports = self.ctx.project_root / "var/reports"
            console.info(f"Reports directory: {reports}", topic="home")

    def _spawn_command(self, command: list[str], *, label: str) -> None:
        try:
            console.info(f"Launching {label}: {' '.join(command)}", topic="home")
            subprocess.Popen(command, cwd=self.ctx.project_root)
        except FileNotFoundError as exc:
            console.error(f"Command failed: {exc}", topic="home")
        except Exception as exc:  # pragma: no cover - defensive
            console.error(f"Unexpected error launching {label}: {exc}", topic="home")


__all__ = ["HomeController", "HomeSummary"]
