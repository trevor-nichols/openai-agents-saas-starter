"""Context and environment helpers for Starter CLI."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values
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
    skip_env: bool = False
    quiet_env: bool = False
    _env_overlay: dict[str, str] = field(default_factory=dict, repr=False)
    _env_backup: dict[str, str] = field(default_factory=dict, repr=False)
    _env_missing: set[str] = field(default_factory=set, repr=False)

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
        overlay: dict[str, str] = {}
        env_files = self.env_files
        if self.skip_env:
            env_files = tuple(
                env_file for env_file in env_files if env_file not in DEFAULT_ENV_FILES
            )
        for env_file in env_files:
            if not env_file.exists():
                continue
            values = dotenv_values(env_file)
            for key, value in values.items():
                if value is None:
                    continue
                overlay[key] = value
            self.loaded_env_files.append(env_file)
            if verbose and on_file_loaded is not None:
                on_file_loaded(env_file)
        self._apply_env_overlay(overlay)

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

    def reset_settings_cache(self) -> None:
        self.settings = None
        try:
            cache_clear = get_settings.cache_clear
        except AttributeError:  # pragma: no cover - defensive
            return
        cache_clear()

    def clear_env_overlay(self) -> None:
        self._apply_env_overlay({})

    def _apply_env_overlay(self, overlay: Mapping[str, str]) -> None:
        removed = set(self._env_overlay.keys()) - set(overlay.keys())
        for key in removed:
            if key in self._env_backup:
                os.environ[key] = self._env_backup[key]
            else:
                os.environ.pop(key, None)

        for key, value in overlay.items():
            if key not in self._env_backup and key not in self._env_missing:
                if key in os.environ:
                    self._env_backup[key] = os.environ[key]
                else:
                    self._env_missing.add(key)
            os.environ[key] = value

        self._env_overlay = dict(overlay)


def build_context(
    *,
    env_files: Sequence[Path] | None = None,
    console: ConsolePort | None = None,
    presenter: Presenter | None = None,
    skip_env: bool = False,
    quiet_env: bool = False,
) -> CLIContext:
    if env_files is None:
        unique_files = DEFAULT_ENV_FILES
    else:
        unique_files = tuple(dict.fromkeys(env_files))
    resolved_console = console or StdConsole()
    resolved_presenter = presenter or build_headless_presenter(resolved_console)
    return CLIContext(
        env_files=unique_files,
        console=resolved_console,
        presenter=resolved_presenter,
        skip_env=skip_env,
        quiet_env=quiet_env,
    )


def iter_env_files(paths: Iterable[str]) -> list[Path]:
    return [Path(path).expanduser().resolve() for path in paths]


def resolve_env_files(
    custom_files: Sequence[Path] | None,
    *,
    skip_defaults: bool,
) -> tuple[Path, ...]:
    custom = tuple(custom_files or ())
    if skip_defaults:
        return custom
    default_paths = list(DEFAULT_ENV_FILES)
    if custom:
        default_paths.extend(custom)
    return tuple(dict.fromkeys(default_paths))


def should_skip_env_loading() -> bool:
    return os.getenv(SKIP_ENV_FLAG, "false").lower() in TRUE_LITERALS


__all__ = [
    "CLIContext",
    "build_context",
    "iter_env_files",
    "resolve_env_files",
    "should_skip_env_loading",
]
