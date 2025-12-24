from __future__ import annotations

import datetime
import os
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import IO

from starter_cli.ports.console import ConsolePort
from starter_cli.services import ops_models

from .models import LaunchResult


@dataclass(frozen=True, slots=True)
class LogLayout:
    base_root: Path
    date_root: Path
    cli_root: Path


def resolve_log_root(
    project_root: Path,
    env: Mapping[str, str],
    *,
    override: Path | None,
) -> Path:
    return ops_models.resolve_log_root_override(project_root, env, override=override)


def ensure_log_layout(base_root: Path, *, today: datetime.date | None = None) -> LogLayout:
    date_value = today or datetime.date.today()
    date_root = base_root / date_value.isoformat()
    cli_root = date_root / "cli"
    try:
        base_root.mkdir(parents=True, exist_ok=True)
        date_root.mkdir(parents=True, exist_ok=True)
        cli_root.mkdir(parents=True, exist_ok=True)
        current_link = base_root / "current"
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()
        current_link.symlink_to(date_root, target_is_directory=True)
    except OSError:
        # Non-fatal; fall back to base_root when symlink fails
        cli_root = base_root
    return LogLayout(base_root=base_root, date_root=date_root, cli_root=cli_root)


def rotate_log(path: Path, *, max_bytes: int = 5_000_000, keep: int = 3) -> None:
    try:
        if not path.exists() or path.stat().st_size < max_bytes:
            return
    except OSError:
        return

    for idx in range(keep - 1, -1, -1):
        src = path if idx == 0 else path.with_name(f"{path.name}.{idx}")
        dest = path.with_name(f"{path.name}.{idx + 1}")
        if src.exists():
            try:
                os.replace(src, dest)
            except OSError:
                continue


class LogSession:
    def __init__(
        self,
        *,
        project_root: Path,
        env: Mapping[str, str],
        override: Path | None,
    ) -> None:
        base_root = resolve_log_root(project_root, env, override=override)
        layout = ensure_log_layout(base_root)
        self.base_log_root = layout.base_root
        self.log_dir = layout.cli_root
        self._log_files: list[IO[str]] = []

    def open_log(self, label: str) -> tuple[Path, IO[str]]:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        path = self.log_dir / f"{label}.log"
        rotate_log(path)
        # append to keep previous runs; rotation keeps size bounded
        fh = open(path, "a", buffering=1, encoding="utf-8")
        self._log_files.append(fh)
        return path, fh

    def start_log_thread(
        self,
        launch: LaunchResult,
        console: ConsolePort,
        stop_event: threading.Event,
    ) -> None:
        if launch.process is None or launch.process.stdout is None:
            return

        def _consume() -> None:
            assert launch.process and launch.process.stdout
            for line in launch.process.stdout:
                if stop_event.is_set():
                    break
                line = line.rstrip()
                if line:
                    launch.log_tail.append(f"{launch.label}: {line}")
                    console.info(f"{launch.label}> {line}")

        threading.Thread(target=_consume, daemon=True).start()

    def dump_tail(self, launches: list[LaunchResult], console: ConsolePort) -> None:
        for launch in launches:
            if launch.log_tail:
                console.info(f"--- last {len(launch.log_tail)} lines from {launch.label} ---")
                for line in launch.log_tail:
                    console.info(line)
            elif launch.log_path and launch.log_path.exists():
                tail = (
                    launch.log_path.read_text(encoding="utf-8", errors="ignore")
                    .splitlines()[-20:]
                )
                if tail:
                    console.info(
                        f"--- last {len(tail)} lines from {launch.label} ({launch.log_path}) ---"
                    )
                    for line in tail:
                        console.info(line)

    def close(self) -> None:
        for fh in self._log_files:
            try:
                fh.close()
            except Exception:
                continue
        self._log_files.clear()


__all__ = [
    "LogLayout",
    "LogSession",
    "ensure_log_layout",
    "resolve_log_root",
    "rotate_log",
]
