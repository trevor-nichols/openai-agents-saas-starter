from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import ClassVar

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from starter_cli.core import CLIContext
from starter_cli.workflows.setup_menu.detection import STALE_AFTER_DAYS, collect_setup_items
from starter_cli.workflows.setup_menu.models import SetupAction, SetupItem


class SetupScreen(Screen[None]):
    """Setup hub screen backed by the existing setup-menu detection logic."""

    BINDINGS: ClassVar = [Binding("enter", "run_selected", "Run", show=True)]

    def __init__(self, ctx: CLIContext, *, stale_days: int = STALE_AFTER_DAYS) -> None:
        super().__init__()
        self.ctx = ctx
        self.stale_window = timedelta(days=stale_days)
        self._items: list[SetupItem] = []

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            DataTable(id="setup-table", zebra_stripes=True),
            Static("", id="setup-status"),
            id="setup-container",
        )
        yield Footer()

    async def on_show(self) -> None:
        await self.refresh_data()

    # ------------------------------------------------------------------
    # Actions dispatched from the app or key bindings
    # ------------------------------------------------------------------
    async def refresh_data(self) -> None:
        table = self.query_one("#setup-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Status", "Setup", "Detail", "Progress", "Last Run")
        await asyncio.to_thread(self._load_items)
        for item in self._items:
            table.add_row(
                _status_badge(item),
                Text(item.label, style="bold"),
                _detail_text(item),
                _progress_text(item),
                _last_run_text(item),
                key=item.key,
            )
        if table.row_count:
            table.focus()
            table.move_cursor(row=0, column=0)
        self._set_status("Press Enter to run the selected setup action; R to refresh; H for home.")

    async def action_run_selected(self) -> None:
        table = self.query_one("#setup-table", DataTable)
        if table.cursor_row is None:
            return
        if table.cursor_row < 0 or table.cursor_row >= len(self._items):
            return
        item = self._items[table.cursor_row]
        if not item or not item.actions:
            self._set_status("No actions available for this setup item.")
            return
        await self._run_action(item.actions[0])
        await self.refresh_data()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_items(self) -> None:
        self._items = list(collect_setup_items(self.ctx, stale_after=self.stale_window))

    async def _run_action(self, action: SetupAction) -> None:
        try:
            self._set_status(f"Running: {' '.join(action.command)}")
            proc = await asyncio.create_subprocess_exec(
                *action.command,
                cwd=self.ctx.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            message = f"{action.label} exited with {proc.returncode}"
            if stdout:
                message += f"\n{stdout.decode().strip()}"
            if stderr:
                message += f"\n{stderr.decode().strip()}"
            self._set_status(message)
        except FileNotFoundError as exc:
            self._set_status(f"Command not found: {exc}")
        except Exception as exc:  # pragma: no cover - defensive
            self._set_status(f"Action failed: {exc}")

    def _set_status(self, message: str) -> None:
        self.query_one("#setup-status", Static).update(Text(message, style="bright_black"))


# ---------------------------------------------------------------------------
# Rendering helpers (Rich inside Textual)
# ---------------------------------------------------------------------------


def _status_badge(item: SetupItem) -> Text:
    styles = {
        "done": ("DONE", "bold green"),
        "partial": ("PARTIAL", "bold yellow"),
        "stale": ("STALE", "yellow"),
        "missing": ("MISSING", "bold red"),
        "failed": ("FAILED", "bold red"),
        "unknown": ("UNKNOWN", "bright_black"),
    }
    label, style = styles.get(item.status, (item.status.upper(), "white"))
    return Text(label, style=style, justify="center")


def _progress_text(item: SetupItem) -> str:
    if item.progress_label:
        return item.progress_label
    if item.progress is None:
        return "—"
    pct = max(0, min(int(item.progress * 100), 100))
    return f"{pct}%"


def _last_run_text(item: SetupItem) -> str:
    return item.last_run.isoformat(timespec="seconds") if item.last_run else "—"


def _detail_text(item: SetupItem) -> Text:
    detail = item.detail or ""
    if item.optional and item.status in {"missing", "unknown"}:
        detail = (detail + " " if detail else "") + "(optional)"
    return Text(detail)


__all__ = ["SetupScreen"]
