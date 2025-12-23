from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class SetupAction:
    key: str
    label: str
    command: Sequence[str] = field(default_factory=tuple)
    route: str | None = None
    warn_overwrite: bool = False


@dataclass(slots=True)
class SetupItem:
    key: str
    label: str
    status: str  # done|partial|missing|stale|failed|unknown
    detail: str | None = None
    progress: float | None = None
    progress_label: str | None = None
    last_run: datetime | None = None
    artifact: Path | None = None
    actions: Sequence[SetupAction] = field(default_factory=tuple)
    optional: bool = False
    metadata: dict[str, str] = field(default_factory=dict)


__all__ = ["SetupAction", "SetupItem"]
