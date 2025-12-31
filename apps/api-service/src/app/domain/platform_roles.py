"""Platform-level roles distinct from tenant membership roles."""

from __future__ import annotations

from enum import Enum


class PlatformRole(str, Enum):
    OPERATOR = "platform_operator"


__all__ = ["PlatformRole"]
