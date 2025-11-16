"""Typed Redis client aliases used across infrastructure modules."""

from __future__ import annotations

from redis.asyncio import Redis

# redis-py 5.x no longer exposes Redis as a Generic, so we keep runtime aliases
# for str/bytes use while preserving intent for type checkers.
RedisStrClient = Redis
RedisBytesClient = Redis

__all__ = ["RedisStrClient", "RedisBytesClient"]
