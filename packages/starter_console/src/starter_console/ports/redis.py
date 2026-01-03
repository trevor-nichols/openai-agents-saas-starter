from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol


class RedisHealthPort(Protocol):
    def ping_all(self, urls: Iterable[str]) -> None: ...


__all__ = ["RedisHealthPort"]
