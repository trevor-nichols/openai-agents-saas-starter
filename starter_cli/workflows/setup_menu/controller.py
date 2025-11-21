from __future__ import annotations

import subprocess
from collections.abc import Iterable
from datetime import timedelta

from rich import box
from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext

from .detection import STALE_AFTER_DAYS, collect_setup_items
from .models import SetupAction, SetupItem


class SetupMenuController:
    def __init__(self, ctx: CLIContext, *, stale_days: int = STALE_AFTER_DAYS) -> None:
        self.ctx = ctx
        self.stale_window = timedelta(days=stale_days)

    def run(self, *, use_tui: bool, output_json: bool) -> int:
        items = collect_setup_items(self.ctx, stale_after=self.stale_window)
        if output_json:
            console._rich_out.print_json(data=_to_dict(items))
            return 0
        if not use_tui:
            self._render_table(items)
            return 0
        self._interactive_loop()
        return 0

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_table(self, items: Iterable[SetupItem], *, show_index: bool = False) -> None:
        table: Table = Table(
            title="Setup Hub",
            box=box.SQUARE,
            show_header=True,
            header_style="bold",
            expand=True,
        )
        if show_index:
            table.add_column("#", justify="right", width=3, no_wrap=True)
        table.add_column("Status", no_wrap=True)
        table.add_column("Setup")
        table.add_column("Detail")
        table.add_column("Progress", no_wrap=True)
        table.add_column("Last Run", no_wrap=True)

        for idx, item in enumerate(items, start=1):
            status = _status_badge(item)
            progress = item.progress_label or _progress_from_float(item.progress)
            last = item.last_run.isoformat(timespec="seconds") if item.last_run else "—"
            detail = item.detail or ""
            if item.optional and item.status in {"missing", "unknown"}:
                detail = (detail + " " if detail else "") + "(optional)"

            label = Text(item.label, style="bold")
            detail_text: RenderableType | str = Text(detail)
            progress_val: RenderableType | str = progress or "—"
            cells: list[RenderableType | str] = [status, label, detail_text, progress_val, last]
            if show_index:
                cells.insert(0, str(idx))
            table.add_row(*cells)

        console.print(table)

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def _interactive_loop(self) -> None:
        console.rule("Setup Hub")
        console.info("Press the item number to run its primary action; R to refresh; Q to quit.")
        items = collect_setup_items(self.ctx, stale_after=self.stale_window)
        while True:
            self._render_table(items, show_index=True)
            choice = console.input("[cyan]Command[/] (#[run], R=refresh, Q=quit): ").strip()
            if not choice:
                continue
            upper = choice.upper()
            if upper == "Q":
                console.note("Exiting setup hub.", topic="setup")
                return
            if upper == "R":
                items = collect_setup_items(self.ctx, stale_after=self.stale_window)
                continue
            if not choice.isdigit():
                console.warn("Enter a number, R, or Q.", topic="setup")
                continue
            idx = int(choice) - 1
            if idx < 0 or idx >= len(items):
                console.warn("Selection out of range.", topic="setup")
                continue
            item = items[idx]
            if not item.actions:
                console.warn("No actions available for this setup.", topic="setup")
                continue
            self._run_action(item.actions[0])
            items = collect_setup_items(self.ctx, stale_after=self.stale_window)

    def _run_action(self, action: SetupAction) -> None:
        if action.warn_overwrite and console._rich_out.is_interactive:
            confirm = console.input(
                f"[yellow]This may overwrite .env files. Proceed with '{action.label}'?[/] (y/N): "
            ).strip()
            if confirm.lower() not in {"y", "yes"}:
                console.note("Cancelled.", topic="setup")
                return
        try:
            console.info(f"Running: {' '.join(action.command)}", topic="setup")
            subprocess.run(
                action.command,
                cwd=self.ctx.project_root,
                check=False,
            )
        except FileNotFoundError as exc:
            console.error(f"Command not found: {exc}", topic="setup")
        except Exception as exc:  # pragma: no cover - defensive
            console.error(f"Action failed: {exc}", topic="setup")


# ---------------------------------------------------------------------------
# Helpers
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


def _progress_from_float(progress: float | None) -> str | None:
    if progress is None:
        return None
    pct = max(0, min(int(progress * 100), 100))
    return f"{pct}%"


def _to_dict(items: Iterable[SetupItem]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for item in items:
        result.append(
            {
                "key": item.key,
                "label": item.label,
                "status": item.status,
                "detail": item.detail,
                "progress": item.progress,
                "progress_label": item.progress_label,
                "last_run": item.last_run.isoformat(timespec="seconds") if item.last_run else None,
                "artifact": str(item.artifact) if item.artifact else None,
                "optional": item.optional,
            }
        )
    return result


__all__ = ["SetupMenuController"]
