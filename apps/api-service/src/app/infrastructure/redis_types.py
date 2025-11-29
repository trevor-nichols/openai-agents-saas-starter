"""Typed Redis client aliases used across infrastructure modules."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

from redis.asyncio import Redis

if TYPE_CHECKING:
    RedisStrClient: TypeAlias = Redis
    RedisBytesClient: TypeAlias = Redis
else:  # pragma: no cover - runtime alias without generics
    RedisStrClient = Redis
    RedisBytesClient = Redis

__all__ = ["RedisStrClient", "RedisBytesClient"]
