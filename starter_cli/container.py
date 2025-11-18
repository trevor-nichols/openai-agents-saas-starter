"""Composition root for Starter CLI."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Iterable

from .adapters.io.console import console, configure_console
from .core import CLIContext, CLIError, build_context, iter_env_files


class ApplicationContainer:
    """Simple service locator for the CLI."""

    def __init__(self) -> None:
        self.console = console

    def configure_console(
        self,
        *,
        theme: str | None,
        width: int | None,
        no_color: bool | None,
    ) -> None:
        configure_console(theme=theme, width=width, no_color=no_color)

    def create_context(self, *, env_files: Sequence[Path] | None = None) -> CLIContext:
        return build_context(env_files=env_files)

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
