from __future__ import annotations

import asyncio
from typing import ClassVar

from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from starter_cli.core import CLIContext
from starter_cli.core.status_models import ActionShortcut, ProbeResult, ServiceStatus
from starter_cli.ui.rich_components import probes_panel, services_table, shortcuts_panel
from starter_cli.workflows.home.doctor import DoctorRunner, detect_profile


def _home_layout(
    probes: list[ProbeResult],
    services: list[ServiceStatus],
    summary: dict[str, int],
    profile: str,
    strict: bool,
    shortcuts: list[ActionShortcut],
) -> Layout:
    """Rich layout for the home dashboard (rendered inside Textual)."""

    layout = Layout(name="root")
    layout.split_column(
        Layout(name="body"),
        Layout(name="footer", size=7),
    )
    show_services = _should_show_services(services)
    if show_services:
        layout["body"].split_row(Layout(name="probes"), Layout(name="services", size=40))
    else:
        layout["body"].split_row(Layout(name="probes"))
    layout["footer"].split_column(
        Layout(name="footer_shortcuts", size=6),
        Layout(name="footer_summary", size=1),
    )
    layout["probes"].update(Panel(probes_panel(probes), title="Probes", border_style="magenta"))
    if show_services:
        layout["services"].update(_services_panel(services))
    layout["footer_shortcuts"].update(_shortcuts_panel(shortcuts))
    layout["footer_summary"].update(_summary_line(summary, profile, strict))
    return layout


def _services_panel(services: list[ServiceStatus]) -> Panel:
    if not services:
        return Panel(Text("No services detected"), title="Services", border_style="cyan")
    return Panel(Group(services_table(services)), title="Services", border_style="cyan")


def _shortcuts_panel(shortcuts: list[ActionShortcut]) -> Panel:
    return Panel(
        shortcuts_panel(shortcuts, bordered=False),
        title="Shortcuts",
        border_style="green",
        padding=(0, 1),
    )


def _summary_line(summary: dict[str, int], profile: str, strict: bool) -> Text:
    text = Text()
    text.append("Profile: ", style="dim")
    text.append(profile, style="bold cyan")
    text.append("  Strict: ", style="dim")
    text.append("yes" if strict else "no", style="bold magenta" if strict else "bold green")
    text.append("  Probes ", style="dim")
    text.append(f"ok={summary.get('ok',0)} ", style="bold green")
    text.append(f"warn={summary.get('warn',0)} ", style="bold yellow")
    text.append(f"error={summary.get('error',0)} ", style="bold red")
    text.append(f"skipped={summary.get('skipped',0)}", style="bright_black")
    return text


def _should_show_services(services: list[ServiceStatus]) -> bool:
    if not services:
        return False
    known_duplicates = {"backend", "frontend"}
    labels = {svc.label for svc in services}
    return any(label not in known_duplicates for label in labels)


class HomeScreen(Screen[None]):
    """Home dashboard screen (Rich layout rendered inside Textual)."""

    BINDINGS: ClassVar = ()

    def __init__(self, ctx: CLIContext) -> None:
        super().__init__()
        self.ctx = ctx
        self._summary: dict[str, int] = {}
        self._probes: list[ProbeResult] = []
        self._services: list[ServiceStatus] = []
        self._profile: str = "local"
        self._strict: bool = False
        self._shortcuts = self._build_shortcuts()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(Static(id="home-body"), id="home-container")
        yield Footer()

    async def on_show(self) -> None:
        await self.refresh_data()

    # ------------------------------------------------------------------
    # Actions dispatched from the app
    # ------------------------------------------------------------------
    async def refresh_data(self) -> None:
        body = self.query_one("#home-body", Static)
        body.update(Text("Refreshing…", style="dim"))
        await asyncio.to_thread(self._collect)
        layout = _home_layout(
            probes=self._probes,
            services=self._services,
            summary=self._summary,
            profile=self._profile,
            strict=self._strict,
            shortcuts=self._shortcuts,
        )
        body.update(layout)

    async def handle_start_dev(self) -> None:
        await self._spawn_process(["python", "-m", "starter_cli.app", "start", "dev"], "start dev")

    async def handle_doctor_strict(self) -> None:
        await self._spawn_process(
            ["python", "-m", "starter_cli.app", "doctor", "--strict"],
            "doctor --strict",
        )

    async def handle_open_reports(self) -> None:
        reports = self.ctx.project_root / "var/reports"
        msg = Text(f"Reports directory: {reports}", style="cyan")
        self.query_one("#home-body", Static).update(msg)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _collect(self) -> None:
        runner = DoctorRunner(self.ctx, profile=detect_profile(), strict=False)
        probes, services, summary = runner.collect()
        self._probes = probes
        self._services = services
        self._summary = summary
        self._profile = runner.profile
        self._strict = runner.strict

    def _build_shortcuts(self) -> list[ActionShortcut]:
        return [
            ActionShortcut(key="H", label="Home", description="Go to home"),
            ActionShortcut(key="S", label="Setup hub", description="Open setup hub"),
            ActionShortcut(key="R", label="Refresh", description="Rerun probes"),
            ActionShortcut(key="G", label="Start dev", description="Run start dev"),
            ActionShortcut(key="D", label="Doctor --strict", description="Run doctor strict"),
            ActionShortcut(key="O", label="Open reports", description="Show reports path"),
            ActionShortcut(key="Q", label="Quit", description="Exit dashboard"),
        ]

    async def _spawn_process(self, command: list[str], label: str) -> None:
        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                cwd=self.ctx.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            fragments: list[str] = [f"{label} exited with {proc.returncode}"]
            if stdout:
                fragments.append(stdout.decode().strip())
            if stderr:
                fragments.append(stderr.decode().strip())
            rendered = Text("\n".join(fragments), style="bright_black")
            self.query_one("#home-body", Static).update(rendered)
        except FileNotFoundError as exc:
            self.query_one("#home-body", Static).update(
                Text(f"Command failed: {exc}", style="red")
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.query_one("#home-body", Static).update(
                Text(f"Unexpected error: {exc}", style="red")
            )


__all__ = ["HomeScreen"]
