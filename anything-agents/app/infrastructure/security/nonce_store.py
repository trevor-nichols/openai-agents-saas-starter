"""Replay-protection helpers for Vault-signed CLI requests."""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from redis.asyncio import Redis

from app.core.config import Settings, get_settings


class NonceStore(Protocol):
    """Protocol describing nonce replay-protection storage."""

    async def check_and_store(self, nonce: str, ttl_seconds: int) -> bool:
        """Return True when nonce is new; False when it already exists."""
        ...


class RedisNonceStore:
    """Redis-backed nonce cache for production usage."""

    def __init__(self, client: Redis, *, prefix: str = "auth:nonce") -> None:
        self._client = client
        self._prefix = prefix

    async def check_and_store(self, nonce: str, ttl_seconds: int) -> bool:
        key = f"{self._prefix}:{nonce}"
        # SET key value EX ttl NX ensures atomic "set if not exists" with TTL.
        result = await self._client.set(key, "1", ex=ttl_seconds, nx=True)
        return bool(result)


@lru_cache
def _build_nonce_store(redis_url: str) -> NonceStore:
    if not redis_url:
        raise RuntimeError("redis_url is required for nonce storage.")
    client = Redis.from_url(redis_url, encoding="utf-8", decode_responses=False)
    return RedisNonceStore(client)


def get_nonce_store(settings: Settings | None = None) -> NonceStore:
    """Retrieve singleton nonce store instance backed by Redis."""

    if settings is None:
        settings = get_settings()
    return _build_nonce_store(settings.redis_url)
