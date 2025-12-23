"""Context and environment helpers for Starter CLI."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from starter_contracts.config import StarterSettingsProtocol, get_settings

from ..ports.console import ConsolePort, StdConsole
from ..ports.presentation import Presenter
from ..presenters.headless import build_headless_presenter
from .constants import DEFAULT_ENV_FILES, PROJECT_ROOT, SKIP_ENV_FLAG, TRUE_LITERALS
from .exceptions import CLIError

EnvFileLoadedHook = Callable[[Path], None]


@dataclass(slots=True)
class CLIContext:
    project_root: Path = PROJECT_ROOT
    env_files: tuple[Path, ...] = DEFAULT_ENV_FILES
    loaded_env_files: list[Path] = field(default_factory=list)
    settings: StarterSettingsProtocol | None = None
    console: ConsolePort = field(default_factory=StdConsole)
    presenter: Presenter | None = None

    def __post_init__(self) -> None:
        if self.presenter is None:
            self.presenter = build_headless_presenter(self.console)

    def load_environment(
        self,
        *,
        verbose: bool = True,
        on_file_loaded: EnvFileLoadedHook | None = None,
    ) -> None:
        """Load environment variables from configured files."""

        self.loaded_env_files.clear()
        for env_file in self.env_files:
            if not env_file.exists():
                continue
            load_dotenv(env_file, override=True)
            self.loaded_env_files.append(env_file)
            if verbose and on_file_loaded is not None:
                on_file_loaded(env_file)

    def optional_settings(self) -> StarterSettingsProtocol | None:
        if self.settings is not None:
            return self.settings
        try:
            self.settings = get_settings()
        except Exception:
            return None
        return self.settings

    def require_settings(self) -> StarterSettingsProtocol:
        settings = self.optional_settings()
        if settings is None:
            raise CLIError(
                "Unable to load application settings. "
                "Ensure .env values are present or pass --env-file explicitly."
            )
        return settings


def build_context(
    *,
    env_files: Sequence[Path] | None = None,
    console: ConsolePort | None = None,
    presenter: Presenter | None = None,
) -> CLIContext:
    if env_files:
        unique_files = tuple(dict.fromkeys(env_files))
    else:
        unique_files = DEFAULT_ENV_FILES
    resolved_console = console or StdConsole()
    resolved_presenter = presenter or build_headless_presenter(resolved_console)
    return CLIContext(
        env_files=unique_files,
        console=resolved_console,
        presenter=resolved_presenter,
    )


def iter_env_files(paths: Iterable[str]) -> list[Path]:
    return [Path(path).expanduser().resolve() for path in paths]


def should_skip_env_loading() -> bool:
    return os.getenv(SKIP_ENV_FLAG, "false").lower() in TRUE_LITERALS


__all__ = [
    "CLIContext",
    "build_context",
    "iter_env_files",
    "should_skip_env_loading",
]
