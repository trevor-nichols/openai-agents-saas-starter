import asyncio
from typing import Any

import pytest
from fakeredis.aioredis import FakeRedis
from redis.exceptions import ConnectionError

from app.services.rate_limit_service import (
    ConcurrencyQuota,
    RateLimiter,
    RateLimitExceeded,
    RateLimitLease,
    RateLimitQuota,
)


@pytest.mark.asyncio
async def test_enforce_quota_blocks_after_limit() -> None:
    limiter = RateLimiter()
    limiter.configure(redis=FakeRedis(), prefix="test", owns_client=False)
    quota = RateLimitQuota(name="chat", limit=1, window_seconds=60)

    await limiter.enforce(quota, ["tenant", "user"])
    with pytest.raises(RateLimitExceeded):
        await limiter.enforce(quota, ["tenant", "user"])


@pytest.mark.asyncio
async def test_concurrency_leases_release_counters() -> None:
    limiter = RateLimiter()
    client = FakeRedis()
    limiter.configure(redis=client, prefix="test", owns_client=False)
    quota = ConcurrencyQuota(name="chat_stream", limit=1, ttl_seconds=30)

    lease = await limiter.acquire_concurrency(quota, ["tenant", "user"])
    assert isinstance(lease, RateLimitLease)

    with pytest.raises(RateLimitExceeded):
        await limiter.acquire_concurrency(quota, ["tenant", "user"])

    await lease.release()

    # After release we should be able to re-acquire the slot.
    new_lease = await limiter.acquire_concurrency(quota, ["tenant", "user"])
    await new_lease.release()


@pytest.mark.asyncio
async def test_concurrency_lease_refreshes_ttl() -> None:
    limiter = RateLimiter()
    client = FakeRedis()
    limiter.configure(redis=client, prefix="test", owns_client=False)
    quota = ConcurrencyQuota(name="chat_stream", limit=1, ttl_seconds=1)

    lease = await limiter.acquire_concurrency(quota, ["tenant", "user"])
    key = "test:concurrency:chat_stream:tenant:user"

    async with lease:
        await asyncio.sleep(1.2)
        ttl = await client.ttl(key)
    assert ttl > 0

    assert not await client.exists(key)


class _FlakyRedis(FakeRedis):
    async def incr(self, *_args: Any, **_kwargs: Any) -> int:
        raise ConnectionError("boom")


@pytest.mark.asyncio
async def test_degrades_open_when_backend_unavailable() -> None:
    limiter = RateLimiter()
    limiter.configure(redis=_FlakyRedis(), prefix="test", owns_client=False)
    quota = RateLimitQuota(name="chat", limit=1, window_seconds=60)

    await limiter.enforce(quota, ["tenant", "user"])

    lease = await limiter.acquire_concurrency(
        ConcurrencyQuota(name="chat_stream", limit=1, ttl_seconds=5),
        ["tenant", "user"],
    )
    assert isinstance(lease, RateLimitLease)
    await lease.release()
