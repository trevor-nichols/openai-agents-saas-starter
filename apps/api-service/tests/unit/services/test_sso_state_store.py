"""Unit tests for Redis-backed SSO state store parsing."""

from __future__ import annotations

import json

import pytest

from typing import cast

from app.infrastructure.redis_types import RedisBytesClient
from app.services.sso.state_store import RedisSsoStateStore


class FakeRedis:
    def __init__(self, value):
        self.value = value

    async def eval(self, *_args, **_kwargs):
        return self.value


@pytest.mark.asyncio
async def test_consume_state_rejects_invalid_json() -> None:
    store = RedisSsoStateStore(cast(RedisBytesClient, FakeRedis(b"not-json")), ttl_seconds=60)
    assert await store.consume_state("state") is None


@pytest.mark.asyncio
async def test_consume_state_rejects_non_dict_payload() -> None:
    store = RedisSsoStateStore(
        cast(RedisBytesClient, FakeRedis(json.dumps(["oops"]).encode("utf-8"))),
        ttl_seconds=60,
    )
    assert await store.consume_state("state") is None


@pytest.mark.asyncio
async def test_consume_state_rejects_invalid_scopes() -> None:
    payload = {
        "provider_key": "google",
        "nonce": "nonce",
        "redirect_uri": "https://app.example.com/auth/sso/google/callback",
        "scopes": "openid email",
    }
    store = RedisSsoStateStore(
        cast(RedisBytesClient, FakeRedis(json.dumps(payload).encode("utf-8"))),
        ttl_seconds=60,
    )
    assert await store.consume_state("state") is None


@pytest.mark.asyncio
async def test_consume_state_parses_valid_payload() -> None:
    payload = {
        "tenant_id": " ",
        "provider_key": "google",
        "pkce_verifier": "",
        "nonce": "nonce",
        "redirect_uri": "https://app.example.com/auth/sso/google/callback",
        "scopes": ["openid", "email", ""],
    }
    store = RedisSsoStateStore(
        cast(RedisBytesClient, FakeRedis(json.dumps(payload).encode("utf-8"))),
        ttl_seconds=60,
    )
    result = await store.consume_state("state")
    assert result is not None
    assert result.tenant_id is None
    assert result.provider_key == "google"
    assert result.pkce_verifier is None
    assert result.scopes == ["openid", "email"]
