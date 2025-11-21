"""Protocols describing billing event streaming backends."""

from __future__ import annotations

from typing import Protocol


class BillingEventStream(Protocol):
    async def next_message(self, timeout: float | None = None) -> str | None:
        ...

    async def close(self) -> None:
        ...


class BillingEventBackend(Protocol):
    async def publish(self, channel: str, message: str) -> None:
        ...

    async def subscribe(self, channel: str) -> BillingEventStream:
        ...

    async def store_bookmark(self, key: str, value: str) -> None:
        ...

    async def load_bookmark(self, key: str) -> str | None:
        ...

    async def close(self) -> None:
        ...
