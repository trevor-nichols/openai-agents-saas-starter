from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import subprocess


@dataclass(slots=True)
class LaunchResult:
    label: str
    command: Sequence[str]
    process: subprocess.Popen[Any] | None
    isolated: bool = False
    pgid: int | None = None
    error: str | None = None
    log_tail: deque[str] = field(default_factory=lambda: deque(maxlen=50))
    log_path: Path | None = None


__all__ = ["LaunchResult"]
