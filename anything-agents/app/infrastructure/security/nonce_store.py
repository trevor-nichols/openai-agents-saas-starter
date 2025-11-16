"""Replay-protection helpers for Vault-signed CLI requests."""

from __future__ import annotations

import asyncio
from threading import Lock
from typing import Protocol, cast

from app.core.config import Settings, get_settings
from app.infrastructure.redis.factory import get_redis_factory
from app.infrastructure.redis_types import RedisBytesClient


class NonceStore(Protocol):
    """Protocol describing nonce replay-protection storage."""

    async def check_and_store(self, nonce: str, ttl_seconds: int) -> bool:
        """Return True when nonce is new; False when it already exists."""
        ...


class RedisNonceStore:
    """Redis-backed nonce cache for production usage."""

    def __init__(self, client: RedisBytesClient, *, prefix: str = "auth:nonce") -> None:
        self._client = client
        self._prefix = prefix

    async def check_and_store(self, nonce: str, ttl_seconds: int) -> bool:
        key = f"{self._prefix}:{nonce}"
        # SET key value EX ttl NX ensures atomic "set if not exists" with TTL.
        result = await self._client.set(key, "1", ex=ttl_seconds, nx=True)
        return bool(result)


_STORE_CACHE_LOCK = Lock()


def _build_nonce_store(settings: Settings) -> RedisNonceStore:
    redis_url = settings.resolve_security_token_redis_url()
    if not redis_url:
        raise RuntimeError(
            "SECURITY_TOKEN_REDIS_URL (or REDIS_URL) is required for nonce storage."
        )
    client = cast(
        RedisBytesClient,
        get_redis_factory(settings).get_client("security_tokens"),
    )
    return RedisNonceStore(client)


def get_nonce_store(settings: Settings | None = None) -> NonceStore:
    """Retrieve singleton nonce store instance backed by Redis."""

    if settings is None:
        settings = get_settings()

    loop = asyncio.get_running_loop()
    cache = getattr(loop, "_nonce_store_cache", None)
    if cache is None:
        cache = {}
        loop._nonce_store_cache = cache  # type: ignore[attr-defined]

    with _STORE_CACHE_LOCK:
        redis_url = settings.resolve_security_token_redis_url()
        if not redis_url:
            raise RuntimeError(
                "SECURITY_TOKEN_REDIS_URL (or REDIS_URL) is required for nonce storage."
            )
        store = cache.get(redis_url)
        if store is None:
            store = _build_nonce_store(settings)
            cache[redis_url] = store
        return store
