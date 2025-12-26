"""Path resolution helpers for repo-root runtime artifacts."""
from __future__ import annotations

from pathlib import Path

# File location: apps/api-service/src/app/core/paths.py
APP_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = APP_ROOT.parent.parent


def resolve_repo_path(raw: str | Path) -> Path:
    """Resolve a path relative to the repo root when not absolute."""

    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


__all__ = ["APP_ROOT", "REPO_ROOT", "resolve_repo_path"]
