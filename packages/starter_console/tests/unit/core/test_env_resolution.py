from __future__ import annotations

from pathlib import Path

from starter_console.core.constants import DEFAULT_ENV_FILES
from starter_console.core.context import resolve_env_files


def test_resolve_env_files_skips_defaults_when_requested() -> None:
    custom = (Path("/tmp/custom.env"),)
    resolved = resolve_env_files(custom, skip_defaults=True)
    assert resolved == custom


def test_resolve_env_files_returns_empty_when_skipping_without_customs() -> None:
    resolved = resolve_env_files((), skip_defaults=True)
    assert resolved == ()


def test_resolve_env_files_includes_defaults_and_customs() -> None:
    custom = (Path("/tmp/custom.env"), Path("/tmp/custom.env"))
    resolved = resolve_env_files(custom, skip_defaults=False)
    assert resolved[: len(DEFAULT_ENV_FILES)] == DEFAULT_ENV_FILES
    assert resolved[-1] == custom[0]
    assert len(set(resolved)) == len(resolved)


def test_resolve_env_files_defaults_only() -> None:
    resolved = resolve_env_files((), skip_defaults=False)
    assert resolved == DEFAULT_ENV_FILES
