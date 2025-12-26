"""Path resolution helpers for repo-root runtime artifacts."""
from __future__ import annotations

from pathlib import Path

# File location: packages/starter_contracts/src/starter_contracts/paths.py
CONTRACTS_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = CONTRACTS_ROOT.parent.parent


def resolve_repo_path(raw: str | Path, *, repo_root: Path | None = None) -> Path:
    """Resolve a path relative to the repo root when not absolute."""

    root = repo_root or REPO_ROOT
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return (root / path).resolve()


__all__ = ["CONTRACTS_ROOT", "REPO_ROOT", "resolve_repo_path"]
