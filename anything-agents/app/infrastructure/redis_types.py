"""Typed Redis client aliases used across infrastructure modules."""

from __future__ import annotations

from redis.asyncio import Redis

RedisStrClient = Redis[str]
RedisBytesClient = Redis[bytes]

__all__ = ["RedisStrClient", "RedisBytesClient"]
