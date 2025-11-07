"""Tests for nonce replay-protection helpers."""

from __future__ import annotations

import asyncio

import pytest
from fakeredis.aioredis import FakeRedis

from app.infrastructure.security.nonce_store import RedisNonceStore


def _build_store() -> RedisNonceStore:
    return RedisNonceStore(FakeRedis())


@pytest.mark.asyncio
async def test_redis_nonce_store_allows_unique_nonces() -> None:
    store = _build_store()

    first = await store.check_and_store("nonce-1", ttl_seconds=2)
    second = await store.check_and_store("nonce-2", ttl_seconds=2)

    assert first is True
    assert second is True


@pytest.mark.asyncio
async def test_redis_nonce_store_rejects_duplicate() -> None:
    store = _build_store()

    assert await store.check_and_store("dup", ttl_seconds=2) is True
    assert await store.check_and_store("dup", ttl_seconds=2) is False


@pytest.mark.asyncio
async def test_redis_nonce_store_expires_entries() -> None:
    store = _build_store()

    assert await store.check_and_store("ephemeral", ttl_seconds=1) is True
    await asyncio.sleep(1.1)
    assert await store.check_and_store("ephemeral", ttl_seconds=1) is True
