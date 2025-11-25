from __future__ import annotations

import importlib
from collections.abc import Iterable
from datetime import timedelta

from rich import box
from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from starter_cli.adapters.io.console import console
from starter_cli.core import CLIContext

from .detection import STALE_AFTER_DAYS, collect_setup_items
from .models import SetupItem

# Exposed for tests; populated at runtime to avoid circular imports.
StarterTUI = None


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
        tui_cls = globals().get("StarterTUI")
        if tui_cls is None:
            module = importlib.import_module("starter_cli.ui")
            tui_cls = module.StarterTUI
            globals()["StarterTUI"] = tui_cls

        tui_cls(self.ctx, initial_screen="setup").run()
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
