"""Unit tests for the Redis client factory."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from app.core.config import Settings
from app.infrastructure.redis.factory import (
    get_redis_factory,
    reset_redis_factory,
)


def build_settings(**overrides: object) -> Settings:
    base = Settings()
    return base.model_copy(update=overrides)


@pytest.fixture(autouse=True)
def _reset_factory() -> Generator[None, None, None]:
    reset_redis_factory()
    yield
    reset_redis_factory()


def test_factory_reuses_clients_per_purpose() -> None:
    settings = build_settings(
        redis_url="redis://shared:6379/0",
        rate_limit_redis_url="redis://ratelimit:6379/1",
        auth_cache_redis_url="redis://auth:6379/2",
        security_token_redis_url="redis://security:6379/3",
        billing_events_redis_url="redis://billing:6379/4",
    )

    factory = get_redis_factory(settings)

    rate_client = factory.get_client("rate_limit")
    assert rate_client is factory.get_client("rate_limit")

    security_bytes = factory.get_client("security_tokens")
    security_str = factory.get_client("security_tokens", decode_responses=True)
    assert security_bytes is not security_str


def test_factory_enforces_tls_outside_safe_environments() -> None:
    settings = build_settings(
        environment="production",
        redis_url="redis://shared:6379/0",
        rate_limit_redis_url="redis://ratelimit:6379/1",
    )

    factory = get_redis_factory(settings)

    with pytest.raises(RuntimeError):
        factory.get_client("rate_limit")


def test_factory_accepts_rediss_with_credentials_in_production() -> None:
    settings = build_settings(
        environment="production",
        redis_url="rediss://:secret@shared:6380/0",
        rate_limit_redis_url="rediss://:secret@ratelimit:6380/1",
    )

    factory = get_redis_factory(settings)

    client = factory.get_client("rate_limit")
    assert client is factory.get_client("rate_limit")
