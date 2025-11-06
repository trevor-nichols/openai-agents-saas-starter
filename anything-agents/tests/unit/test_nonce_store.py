"""Tests for nonce replay-protection helpers."""

from __future__ import annotations

import asyncio

import pytest

from app.infrastructure.security.nonce_store import InMemoryNonceStore


@pytest.mark.asyncio
async def test_in_memory_nonce_store_allows_unique_nonces() -> None:
    store = InMemoryNonceStore()

    first = await store.check_and_store("nonce-1", ttl_seconds=2)
    second = await store.check_and_store("nonce-2", ttl_seconds=2)

    assert first is True
    assert second is True


@pytest.mark.asyncio
async def test_in_memory_nonce_store_rejects_duplicate() -> None:
    store = InMemoryNonceStore()

    assert await store.check_and_store("dup", ttl_seconds=2) is True
    assert await store.check_and_store("dup", ttl_seconds=2) is False


@pytest.mark.asyncio
async def test_in_memory_nonce_store_expires_entries() -> None:
    store = InMemoryNonceStore()

    assert await store.check_and_store("ephemeral", ttl_seconds=1) is True
    await asyncio.sleep(1.1)
    assert await store.check_and_store("ephemeral", ttl_seconds=1) is True

