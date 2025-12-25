from __future__ import annotations

from pathlib import Path

from starter_console.core import CLIContext


def ensure_summary_paths(
    ctx: CLIContext,
    summary_path: Path | None,
    markdown_summary_path: Path | None,
) -> tuple[Path, Path]:
    summary = summary_path or (ctx.project_root / "var/reports/setup-summary.json")
    summary.parent.mkdir(parents=True, exist_ok=True)
    markdown = markdown_summary_path or (
        ctx.project_root / "var/reports/cli-one-stop-summary.md"
    )
    markdown.parent.mkdir(parents=True, exist_ok=True)
    return summary, markdown


__all__ = ["ensure_summary_paths"]
