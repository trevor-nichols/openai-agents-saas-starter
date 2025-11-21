from __future__ import annotations

import inspect
from typing import Any, ClassVar

from textual.app import App
from textual.binding import Binding

from starter_cli.core import CLIContext

from .pages.home import HomeScreen
from .pages.setup import SetupScreen


class StarterTUI(App[None]):
    """Unified Textual TUI for the Starter CLI.

    The app registers multiple screens (home, setup hub, future pages) and
    exposes a small set of global keybindings. Screen-specific actions are
    delegated to the active screen when present.
    """

    CSS_PATH: ClassVar[str | None] = None  # keep styling inline for now

    BINDINGS: ClassVar = [
        Binding("h", "go_home", "Home", show=True),
        Binding("s", "go_setup", "Setup", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("g", "start_dev", "Start Dev", show=False),
        Binding("d", "doctor_strict", "Doctor Strict", show=False),
        Binding("o", "open_reports", "Reports", show=False),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, ctx: CLIContext, *, initial_screen: str = "home") -> None:
        self.ctx = ctx
        self._initial_screen = initial_screen
        super().__init__()

    def on_mount(self) -> None:
        # Install screens up front so navigation is cheap and predictable.
        self.install_screen(HomeScreen(self.ctx), name="home")
        self.install_screen(SetupScreen(self.ctx), name="setup")
        self._ensure_screen(self._initial_screen)

    # ------------------------------------------------------------------
    # Global actions
    # ------------------------------------------------------------------
    async def action_go_home(self) -> None:
        self._ensure_screen("home")

    async def action_go_setup(self) -> None:
        self._ensure_screen("setup")

    async def action_refresh(self) -> None:
        await self._dispatch_to_screen("refresh_data")

    async def action_start_dev(self) -> None:
        await self._dispatch_to_screen("handle_start_dev")

    async def action_doctor_strict(self) -> None:
        await self._dispatch_to_screen("handle_doctor_strict")

    async def action_open_reports(self) -> None:
        await self._dispatch_to_screen("handle_open_reports")

    async def action_quit(self) -> None:
        self.exit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    async def _dispatch_to_screen(self, method: str) -> None:
        try:
            current = self.screen
        except Exception:
            return
        target = getattr(current, method, None)
        if not callable(target):
            return
        result: Any = target()
        if inspect.isawaitable(result):
            await result

    def _ensure_screen(self, name: str) -> None:
        """Switch to a screen, pushing it first when the stack is empty."""

        try:
            self.switch_screen(name)
            return
        except Exception:
            # stack may be empty; fall back to push
            try:
                self.push_screen(name)
            except Exception:
                return


__all__ = ["StarterTUI"]
