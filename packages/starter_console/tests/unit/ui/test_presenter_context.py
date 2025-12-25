from __future__ import annotations

from pathlib import Path

from starter_console.core import CLIContext
from starter_console.presenters.headless import build_headless_presenter
from starter_console.ports.console import StdConsole
from starter_console.ui.context import derive_presenter_context


def test_derive_presenter_context_carries_env_flags(tmp_path: Path) -> None:
    ctx = CLIContext(
        project_root=tmp_path,
        env_files=(tmp_path / ".env.local", tmp_path / ".env"),
        loaded_env_files=[tmp_path / ".env.local"],
        skip_env=True,
        quiet_env=True,
    )
    console = StdConsole()
    presenter = build_headless_presenter(console)

    derived = derive_presenter_context(ctx, console=console, presenter=presenter)

    assert derived.env_files == ctx.env_files
    assert derived.loaded_env_files == ctx.loaded_env_files
    assert derived.loaded_env_files is not ctx.loaded_env_files
    assert derived.skip_env is True
    assert derived.quiet_env is True
