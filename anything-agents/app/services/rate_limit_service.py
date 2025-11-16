"""Redis-backed rate limiting helpers for API endpoints."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from types import TracebackType

from redis.exceptions import RedisError

from app.infrastructure.redis_types import RedisBytesClient


@dataclass(slots=True, frozen=True)
class RateLimitQuota:
    """Fixed-window quota definition."""

    name: str
    limit: int
    window_seconds: int
    scope: str = "user"


@dataclass(slots=True, frozen=True)
class ConcurrencyQuota:
    """Concurrent-connection quota definition."""

    name: str
    limit: int
    ttl_seconds: int
    scope: str = "user"


class RateLimitExceeded(RuntimeError):
    """Raised when a caller exceeds a configured quota."""

    def __init__(self, *, quota: str, limit: int, retry_after: int, scope: str) -> None:
        self.quota = quota
        self.limit = limit
        self.retry_after = max(retry_after, 1)
        self.scope = scope
        super().__init__(f"Rate limit exceeded for '{quota}'")


class RateLimitLease:
    """RAII helper ensuring concurrency counters are alive until released."""

    __slots__ = ("_redis", "_key", "_released", "_ttl", "_heartbeat", "_stop")

    def __init__(
        self, redis: RedisBytesClient | None, key: str | None, ttl_seconds: int | None = None
    ) -> None:
        self._redis = redis
        self._key = key
        self._released = False
        self._ttl = float(ttl_seconds or 0)
        self._heartbeat: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    async def release(self) -> None:
        if self._released:
            return
        self._released = True
        self._stop.set()
        if self._heartbeat:
            self._heartbeat.cancel()
            try:
                await self._heartbeat
            except asyncio.CancelledError:  # pragma: no cover - expected
                pass
        if not self._redis or not self._key:
            return
        value = await self._redis.decr(self._key)
        if value <= 0:
            await self._redis.delete(self._key)

    async def __aenter__(self) -> RateLimitLease:
        if self._redis and self._key and self._ttl > 0:
            interval = max(self._ttl / 2, 0.5)
            self._heartbeat = asyncio.create_task(self._refresh_loop(interval))
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.release()

    async def _refresh_loop(self, interval: float) -> None:
        try:
            while not self._stop.is_set():
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=interval)
                    break
                except TimeoutError:
                    if self._redis and self._key:
                        await self._redis.expire(self._key, int(max(self._ttl, 1)))
        except asyncio.CancelledError:  # pragma: no cover - expected
            pass


class RateLimiter:
    """Redis-backed rate limit manager."""

    def __init__(self) -> None:
        self._redis: RedisBytesClient | None = None
        self._prefix = "rate-limit"
        self._owns_client = False
        self._logger = logging.getLogger(__name__)

    def configure(
        self,
        *,
        redis: RedisBytesClient,
        prefix: str = "rate-limit",
        owns_client: bool = True,
    ) -> None:
        self._redis = redis
        self._prefix = prefix.strip() or "rate-limit"
        self._owns_client = owns_client

    async def shutdown(self) -> None:
        if self._redis and self._owns_client:
            await self._redis.close()
        self._redis = None
        self._owns_client = False

    def reset(self) -> None:
        """Detach any configured backend without closing it (used in tests)."""

        self._redis = None
        self._owns_client = False

    async def enforce(self, quota: RateLimitQuota, key_parts: Sequence[str]) -> None:
        if not self._redis or quota.limit <= 0:
            return
        key = self._composite_key("quota", quota.name, key_parts)
        try:
            current = await self._redis.incr(key)
            if current == 1:
                await self._redis.expire(key, quota.window_seconds)
            if current > quota.limit:
                retry_after = await self._remaining_ttl(key, quota.window_seconds)
                raise RateLimitExceeded(
                    quota=quota.name,
                    limit=quota.limit,
                    retry_after=retry_after,
                    scope=quota.scope,
                )
        except RedisError as exc:  # pragma: no cover - redis outage path
            self._logger.warning(
                "Rate limiter unavailable; allowing traffic (quota=%s)",
                quota.name,
                exc_info=exc,
            )

    async def acquire_concurrency(
        self,
        quota: ConcurrencyQuota,
        key_parts: Sequence[str],
    ) -> RateLimitLease:
        if not self._redis or quota.limit <= 0:
            return RateLimitLease(None, None)
        key = self._composite_key("concurrency", quota.name, key_parts)
        try:
            current = await self._redis.incr(key)
            await self._redis.expire(key, max(quota.ttl_seconds, 1))
            if current > quota.limit:
                await self._redis.decr(key)
                retry_after = await self._remaining_ttl(key, quota.ttl_seconds)
                raise RateLimitExceeded(
                    quota=quota.name,
                    limit=quota.limit,
                    retry_after=retry_after,
                    scope=quota.scope,
                )
        except RedisError as exc:  # pragma: no cover - redis outage path
            self._logger.warning(
                "Rate limiter unavailable; allowing traffic (quota=%s)",
                quota.name,
                exc_info=exc,
            )
            return RateLimitLease(None, None)
        return RateLimitLease(self._redis, key, quota.ttl_seconds)

    async def _remaining_ttl(self, key: str, fallback: int) -> int:
        if not self._redis:
            return fallback
        ttl = await self._redis.ttl(key)
        if ttl is None or ttl < 0:
            return fallback
        return ttl or fallback

    def _composite_key(self, prefix: str, quota_name: str, parts: Sequence[str]) -> str:
        segments: list[str] = [self._prefix, prefix, quota_name]
        segments.extend(self._sanitize_parts(parts))
        return ":".join(segments)

    @staticmethod
    def _sanitize_parts(parts: Sequence[str]) -> Iterable[str]:
        for part in parts:
            yield (part or "unknown").replace(" ", "_")


def get_rate_limiter() -> RateLimiter:
    """Resolve the configured rate limiter instance."""

    from app.bootstrap.container import get_container

    return get_container().rate_limiter


class _RateLimiterHandle:
    """Proxy exposing the active rate limiter."""

    def __getattr__(self, name: str):
        return getattr(get_rate_limiter(), name)


rate_limiter = _RateLimiterHandle()
