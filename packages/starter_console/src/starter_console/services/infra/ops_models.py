from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

DEFAULT_LOG_ROOT = Path("var/log")

@dataclass(frozen=True, slots=True)
class LogEntry:
    name: str
    path: Path
    exists: bool


def resolve_log_root(project_root: Path, env: Mapping[str, str]) -> Path:
    raw = env.get("LOG_ROOT") or str(DEFAULT_LOG_ROOT)
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()
    return candidate


def resolve_log_root_override(
    project_root: Path,
    env: Mapping[str, str],
    *,
    override: Path | None,
) -> Path:
    if override is not None:
        candidate = override.expanduser()
        if not candidate.is_absolute():
            candidate = (project_root / candidate).resolve()
        return candidate
    return resolve_log_root(project_root, env)


def resolve_active_log_dir(log_root: Path) -> Path:
    current = log_root / "current"
    if current.exists():
        return current.resolve()
    if not log_root.exists():
        return log_root
    dated_dirs = [
        entry
        for entry in log_root.iterdir()
        if entry.is_dir() and _is_date_dir(entry.name)
    ]
    if not dated_dirs:
        return log_root
    latest = max(dated_dirs, key=lambda entry: entry.name)
    return latest.resolve()


def collect_log_entries(log_dir: Path) -> list[LogEntry]:
    entries: list[LogEntry] = []
    candidates = {
        "api/all.log": log_dir / "api" / "all.log",
        "api/error.log": log_dir / "api" / "error.log",
        "frontend/all.log": log_dir / "frontend" / "all.log",
        "frontend/error.log": log_dir / "frontend" / "error.log",
    }
    for name, path in candidates.items():
        entries.append(LogEntry(name=name, path=path, exists=path.exists()))

    cli_dir = log_dir / "cli"
    cli_files = list(cli_dir.glob("*.log")) if cli_dir.exists() else []
    entries.append(
        LogEntry(
            name="cli/*.log",
            path=cli_dir,
            exists=bool(cli_files),
        )
    )
    return entries


def mask_value(value: str | None) -> str:
    if not value:
        return "(missing)"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _is_date_dir(name: str) -> bool:
    try:
        date.fromisoformat(name)
    except ValueError:
        return False
    return True


__all__ = [
    "DEFAULT_LOG_ROOT",
    "LogEntry",
    "collect_log_entries",
    "mask_value",
    "resolve_active_log_dir",
    "resolve_log_root",
    "resolve_log_root_override",
]
