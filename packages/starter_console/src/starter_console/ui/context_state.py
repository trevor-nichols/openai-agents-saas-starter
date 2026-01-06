from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from textual.message import Message

from starter_console.core import CLIContext
from starter_console.core.constants import DEFAULT_ENV_FILES


@dataclass(frozen=True, slots=True)
class EnvReloadedPayload:
    env_files: tuple[Path, ...]
    skip_env: bool
    quiet_env: bool
    loaded_files: tuple[Path, ...]


class EnvReloaded(Message):
    def __init__(self, payload: EnvReloadedPayload) -> None:
        self.payload = payload
        super().__init__()


class ContextState:
    def __init__(self, ctx: CLIContext) -> None:
        self.ctx = ctx
        self._default_env_files = list(DEFAULT_ENV_FILES)
        seen = set(DEFAULT_ENV_FILES)
        custom: list[Path] = []
        for path in ctx.env_files:
            if path in seen:
                continue
            custom.append(path)
            seen.add(path)
        self._custom_env_files = custom
        self._sync_env_files()

    @property
    def default_env_files(self) -> list[Path]:
        return list(self._default_env_files)

    @property
    def custom_env_files(self) -> list[Path]:
        return list(self._custom_env_files)

    def add_custom(self, raw: str) -> tuple[bool, str]:
        value = raw.strip()
        if not value:
            return False, "Provide a path to add."
        path = Path(value).expanduser().resolve()
        if path in self._default_env_files:
            return False, "Defaults are managed by Skip env load; add custom env files only."
        if path in self._custom_env_files:
            return False, "Env file already listed."
        self._custom_env_files.append(path)
        self._sync_env_files()
        return True, f"Added {path}."

    def remove_custom(self, index: int) -> tuple[bool, str, Path | None]:
        if index < 0 or index >= len(self._custom_env_files):
            return False, "Select a custom env file row to remove.", None
        removed = self._custom_env_files.pop(index)
        self._sync_env_files()
        return True, f"Removed {removed}.", removed

    def reload_env(self, *, skip_env: bool, quiet_env: bool) -> tuple[str, EnvReloadedPayload]:
        self.ctx.skip_env = skip_env
        self.ctx.quiet_env = quiet_env
        self._sync_env_files()
        self.ctx.load_environment(verbose=not quiet_env)
        self.ctx.reset_settings_cache()
        loaded_count = len(self.ctx.loaded_env_files)
        if skip_env:
            if loaded_count:
                status = f"Defaults skipped; loaded {loaded_count} custom env file(s)."
            else:
                status = "Defaults skipped; no custom env files loaded."
        else:
            status = "Env files loaded."
        payload = EnvReloadedPayload(
            env_files=tuple(self._default_env_files + self._custom_env_files),
            skip_env=skip_env,
            quiet_env=quiet_env,
            loaded_files=tuple(self.ctx.loaded_env_files),
        )
        return status, payload

    def summary(self) -> str:
        profile, source = self._resolve_profile()
        source_label = f" ({source})" if source else ""
        default_count = len(self._default_env_files)
        custom_count = len(self._custom_env_files)
        loaded = len(self.ctx.loaded_env_files)
        total = default_count + custom_count
        return (
            f"Env: {profile}{source_label} | files: {total} (loaded {loaded}) | "
            f"skip defaults: {'yes' if self.ctx.skip_env else 'no'} | "
            f"quiet: {'yes' if self.ctx.quiet_env else 'no'}"
        )

    def _sync_env_files(self) -> None:
        self.ctx.env_files = tuple(self._default_env_files + self._custom_env_files)

    def _resolve_profile(self) -> tuple[str, str]:
        settings = self.ctx.optional_settings()
        if settings is not None:
            value = getattr(settings, "environment", None)
            if value:
                return str(value), "settings"
        env_value = os.getenv("ENVIRONMENT")
        if env_value:
            return env_value, "env"
        return "development", "default"


__all__ = ["ContextState", "EnvReloaded", "EnvReloadedPayload"]
