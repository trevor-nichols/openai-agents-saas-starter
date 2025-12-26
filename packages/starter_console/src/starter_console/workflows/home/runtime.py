from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from starter_console.core import CLIContext
from starter_console.services.infra import ops_models

DEFAULT_PIDFILE_RELATIVE = Path("var/run/stack.json")


@dataclass(frozen=True, slots=True)
class StackRuntimeConfig:
    pidfile: Path
    log_root: Path


def resolve_pidfile(project_root: Path, override: Path | None = None) -> Path:
    if override is None:
        return (project_root / DEFAULT_PIDFILE_RELATIVE).resolve()
    candidate = override.expanduser()
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()
    return candidate


def resolve_log_root(
    project_root: Path,
    env: Mapping[str, str],
    *,
    override: Path | None = None,
) -> Path:
    return ops_models.resolve_log_root_override(project_root, env, override=override)


def resolve_stack_runtime(
    ctx: CLIContext,
    *,
    pidfile_override: Path | None = None,
    log_dir_override: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> StackRuntimeConfig:
    env_map = env or os.environ
    return StackRuntimeConfig(
        pidfile=resolve_pidfile(ctx.project_root, pidfile_override),
        log_root=resolve_log_root(ctx.project_root, env_map, override=log_dir_override),
    )


__all__ = [
    "DEFAULT_PIDFILE_RELATIVE",
    "StackRuntimeConfig",
    "resolve_log_root",
    "resolve_pidfile",
    "resolve_stack_runtime",
]
