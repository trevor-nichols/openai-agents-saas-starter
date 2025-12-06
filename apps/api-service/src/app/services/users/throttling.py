"""Login throttling strategies."""

from __future__ import annotations

from typing import Protocol, cast

from app.infrastructure.redis.factory import get_redis_factory
from app.infrastructure.redis_types import RedisBytesClient
from app.observability.logging import log_event

from .errors import IpThrottledError


class LoginThrottle(Protocol):
    async def ensure_allowed(self, ip_address: str | None) -> None: ...

    async def register_failure(self, ip_address: str | None) -> None: ...


class NullLoginThrottle(LoginThrottle):
    async def ensure_allowed(self, ip_address: str | None) -> None:  # pragma: no cover - noop
        return None

    async def register_failure(self, ip_address: str | None) -> None:  # pragma: no cover - noop
        return None


class RedisLoginThrottle(LoginThrottle):
    def __init__(
        self,
        client: RedisBytesClient,
        *,
        threshold: int,
        window_seconds: int,
        block_seconds: int,
    ) -> None:
        self._client = client
        self._threshold = max(threshold, 1)
        self._window = max(window_seconds, 1)
        self._block = max(block_seconds, 1)

    async def ensure_allowed(self, ip_address: str | None) -> None:
        if not ip_address:
            return
        for token in self._tokens(ip_address):
            if await self._client.exists(self._block_key(token)):
                raise IpThrottledError("Too many login attempts from this network segment.")

    async def register_failure(self, ip_address: str | None) -> None:
        if not ip_address:
            return
        for token in self._tokens(ip_address):
            counter = self._counter_key(token)
            attempts = await self._client.incr(counter)
            if attempts == 1:
                await self._client.expire(counter, self._window)
            if attempts >= self._threshold:
                await self._client.set(self._block_key(token), b"1", ex=self._block)
                await self._client.delete(counter)
                log_event("auth.ip_lockout", token=token, threshold=self._threshold)

    def _tokens(self, ip_address: str) -> list[str]:
        if ":" in ip_address:
            return [ip_address]
        parts = ip_address.split(".")
        if len(parts) >= 3:
            subnet = ".".join(parts[:3]) + ".0/24"
            return [ip_address, subnet]
        return [ip_address]

    def _counter_key(self, token: str) -> str:
        return f"auth:ip:counter:{token}"

    def _block_key(self, token: str) -> str:
        return f"auth:ip:block:{token}"


def build_ip_throttler(settings) -> LoginThrottle:
    redis_url = settings.resolve_auth_cache_redis_url()
    if not redis_url:
        raise RuntimeError("AUTH_CACHE_REDIS_URL (or REDIS_URL) is required for IP throttling.")
    client = cast(RedisBytesClient, get_redis_factory(settings).get_client("auth_cache"))
    window_seconds = int(settings.auth_ip_lockout_window_minutes * 60)
    block_seconds = int(settings.auth_ip_lockout_duration_minutes * 60)
    return RedisLoginThrottle(
        client,
        threshold=settings.auth_ip_lockout_threshold,
        window_seconds=window_seconds,
        block_seconds=block_seconds,
    )


__all__ = [
    "LoginThrottle",
    "NullLoginThrottle",
    "RedisLoginThrottle",
    "build_ip_throttler",
]
