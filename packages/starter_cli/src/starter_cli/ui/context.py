from __future__ import annotations

from starter_cli.core import CLIContext
from starter_cli.ports.console import ConsolePort
from starter_cli.ports.presentation import Presenter


def derive_presenter_context(
    ctx: CLIContext,
    *,
    console: ConsolePort,
    presenter: Presenter,
) -> CLIContext:
    return CLIContext(
        project_root=ctx.project_root,
        env_files=ctx.env_files,
        loaded_env_files=list(ctx.loaded_env_files),
        settings=ctx.settings,
        console=console,
        presenter=presenter,
        skip_env=ctx.skip_env,
        quiet_env=ctx.quiet_env,
    )


__all__ = ["derive_presenter_context"]
