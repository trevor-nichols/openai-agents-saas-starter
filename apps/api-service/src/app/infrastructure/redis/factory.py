"""Purpose-scoped Redis client factory with TLS/auth enforcement."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Literal, cast
from urllib.parse import urlparse

from redis.asyncio import Redis

from app.core.settings import Settings, get_settings
from app.infrastructure.redis_types import RedisBytesClient, RedisStrClient

RedisPurpose = Literal[
    "rate_limit",
    "auth_cache",
    "security_tokens",
    "billing_events",
    "usage_cache",
]
RedisClient = RedisBytesClient | RedisStrClient


class RedisClientFactory:
    """Build and cache Redis clients per purpose and decode mode."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._logger = logging.getLogger("app.infrastructure.redis.factory")
        self._clients: dict[tuple[RedisPurpose, bool], RedisClient] = {}

    def get_client(self, purpose: RedisPurpose, *, decode_responses: bool = False) -> RedisClient:
        """Return (and memoize) a Redis client for the given purpose."""

        url = self._resolve_url(purpose)
        cache_key: tuple[RedisPurpose, bool] = (purpose, decode_responses)
        client = self._clients.get(cache_key)
        if client is None:
            if decode_responses:
                client = Redis.from_url(
                    url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            else:
                client = Redis.from_url(
                    url,
                    encoding="utf-8",
                    decode_responses=False,
                )
            self._clients[cache_key] = client
        return client

    async def shutdown(self) -> None:
        """Close all managed clients."""

        while self._clients:
            _, client = self._clients.popitem()
            try:
                close_candidate = getattr(client, "aclose", None)
                if not callable(close_candidate):
                    close_candidate = getattr(client, "close", None)

                if callable(close_candidate):
                    close_fn = cast(Callable[[], Awaitable[None]], close_candidate)
                    await close_fn()
                else:  # pragma: no cover - defensive logging
                    self._logger.warning("Redis client is missing close/aclose methods")
            except Exception as exc:  # pragma: no cover - defensive logging
                self._logger.warning("Failed to close Redis client", exc_info=exc)

    def _resolve_url(self, purpose: RedisPurpose) -> str:
        resolver_map: dict[RedisPurpose, Callable[[], str | None]] = {
            "rate_limit": self._settings.resolve_rate_limit_redis_url,
            "auth_cache": self._settings.resolve_auth_cache_redis_url,
            "security_tokens": self._settings.resolve_security_token_redis_url,
            "billing_events": self._settings.resolve_billing_events_redis_url,
            "usage_cache": self._settings.resolve_usage_guardrail_redis_url,
        }
        resolver = resolver_map[purpose]
        url = resolver()
        if not url:
            raise RuntimeError(
                f"No Redis URL configured for '{purpose}' workloads. "
                "Set the dedicated variable or REDIS_URL."
            )
        self._enforce_security(url, purpose)
        return url

    def _enforce_security(self, url: str, purpose: RedisPurpose) -> None:
        if not self._settings.require_hardened_redis():
            return
        parsed = urlparse(url)
        if parsed.scheme != "rediss":
            raise RuntimeError(
                f"{purpose} Redis URL must use rediss:// when "
                f"ENVIRONMENT={self._settings.environment}."
            )
        if parsed.hostname not in {"localhost", "127.0.0.1"} and parsed.password is None:
            raise RuntimeError(
                f"{purpose} Redis URL must include credentials outside local/dev environments."
            )


_FACTORY: RedisClientFactory | None = None


def get_redis_factory(settings: Settings | None = None) -> RedisClientFactory:
    """Return the shared Redis client factory, instantiating lazily."""

    global _FACTORY
    if _FACTORY is None:
        resolved = settings or get_settings()
        _FACTORY = RedisClientFactory(resolved)
    return _FACTORY


def reset_redis_factory() -> None:
    """Forget the cached factory without awaiting shutdown (tests)."""

    global _FACTORY
    _FACTORY = None


async def shutdown_redis_factory() -> None:
    """Close cached clients and clear the factory reference."""

    global _FACTORY
    if _FACTORY is None:
        return
    await _FACTORY.shutdown()
    _FACTORY = None


__all__ = [
    "RedisClientFactory",
    "RedisPurpose",
    "get_redis_factory",
    "reset_redis_factory",
    "shutdown_redis_factory",
]
