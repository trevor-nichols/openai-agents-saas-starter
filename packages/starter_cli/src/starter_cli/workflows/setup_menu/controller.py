from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta

from starter_cli.core import CLIContext
from starter_cli.services.hub import HubService

from .detection import STALE_AFTER_DAYS
from .models import SetupItem


class SetupMenuController:
    def __init__(self, ctx: CLIContext, *, stale_days: int = STALE_AFTER_DAYS) -> None:
        self.ctx = ctx
        self.stale_window = timedelta(days=stale_days)

    def run(self, *, output_json: bool) -> int:
        console = self.ctx.console
        items = HubService(self.ctx).load_setup(stale_days=self.stale_window.days).items
        if output_json:
            import json

            json.dump(_to_dict(items), console.stream, indent=2)
            console.stream.write("\n")
            return 0
        self._render_table(console, items)
        return 0

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_table(
        self,
        console,
        items: Iterable[SetupItem],
        *,
        show_index: bool = False,
    ) -> None:
        headers = ["Status", "Setup", "Detail", "Progress", "Last Run"]
        rows: list[list[str]] = []
        for idx, item in enumerate(items, start=1):
            status = _status_label(item)
            progress = item.progress_label or _progress_from_float(item.progress) or "-"
            last = item.last_run.isoformat(timespec="seconds") if item.last_run else "-"
            detail = item.detail or ""
            if item.optional and item.status in {"missing", "unknown"}:
                detail = (detail + " " if detail else "") + "(optional)"
            row = [status, item.label, detail or "-", progress, last]
            if show_index:
                row.insert(0, str(idx))
            rows.append(row)

        if show_index:
            headers = ["#", *headers]

        lines = _format_table(headers, rows)
        for line in lines:
            console.print(line)



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _status_label(item: SetupItem) -> str:
    labels = {
        "done": "DONE",
        "partial": "PARTIAL",
        "stale": "STALE",
        "missing": "MISSING",
        "failed": "FAILED",
        "unknown": "UNKNOWN",
    }
    return labels.get(item.status, item.status.upper())


def _progress_from_float(progress: float | None) -> str | None:
    if progress is None:
        return None
    pct = max(0, min(int(progress * 100), 100))
    return f"{pct}%"


def _format_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def fmt_row(row: list[str]) -> str:
        padded = [cell.ljust(widths[idx]) for idx, cell in enumerate(row)]
        return " | ".join(padded)

    line = "-+-".join("-" * width for width in widths)
    output = [fmt_row(headers), line]
    output.extend(fmt_row(row) for row in rows)
    return output


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
