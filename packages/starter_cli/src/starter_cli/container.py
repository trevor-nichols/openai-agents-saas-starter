"""Composition root for Starter CLI."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import cast

from .adapters.io.console import console as shared_console
from .core import CLIContext, CLIError, build_context, iter_env_files
from .ports.console import ConsolePort


class ApplicationContainer:
    """Simple service locator for the CLI."""

    def __init__(self) -> None:
        self.console = shared_console

    def create_context(
        self,
        *,
        env_files: Sequence[Path] | None = None,
        skip_env: bool = False,
        quiet_env: bool = False,
    ) -> CLIContext:
        return build_context(
            env_files=env_files,
            console=cast(ConsolePort, self.console),
            skip_env=skip_env,
            quiet_env=quiet_env,
        )

    def iter_env_files(self, paths: Iterable[str]) -> list[Path]:
        return iter_env_files(paths)

    def load_environment(self, ctx: CLIContext, *, verbose: bool) -> None:
        ctx.load_environment(
            verbose=verbose,
            on_file_loaded=lambda path: self.console.info(
                f"Loaded environment from {path}", topic="env"
            ),
        )


def build_container() -> ApplicationContainer:
    return ApplicationContainer()


__all__ = ["ApplicationContainer", "CLIContext", "CLIError", "build_container"]
