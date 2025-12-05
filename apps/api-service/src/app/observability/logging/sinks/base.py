"""Common types for sink builders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.core.settings import Settings


@dataclass(slots=True)
class SinkConfig:
    handlers: dict[str, Any]
    root_handlers: list[str]


class SinkBuilder(Protocol):
    def __call__(
        self,
        settings: Settings,
        log_level: str,
        formatter_ref: str,
        *,
        file_selected: bool,
    ) -> SinkConfig: ...


__all__ = ["SinkBuilder", "SinkConfig"]
