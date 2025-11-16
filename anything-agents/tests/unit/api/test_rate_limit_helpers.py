from __future__ import annotations

import pytest

from app.api.v1.auth import rate_limit_helpers as helpers
from app.services.rate_limit_service import RateLimitExceeded, RateLimitQuota


class _LimiterStub:
    async def enforce(self, quota: RateLimitQuota, key_parts: list[str]) -> None:
        raise RateLimitExceeded(
            quota=quota.name,
            limit=quota.limit,
            retry_after=quota.window_seconds,
            scope=quota.scope,
        )


@pytest.mark.asyncio
async def test_apply_signup_quota_uses_explicit_tenant(monkeypatch):
    limiter = _LimiterStub()
    monkeypatch.setattr(helpers, "rate_limiter", limiter)
    monkeypatch.setattr(helpers, "record_signup_blocked", lambda *, reason: None)
    monkeypatch.setattr(helpers, "record_signup_attempt", lambda *, result, policy: None)

    observed: dict[str, str] = {}

    def fake_raise(_: RateLimitExceeded, *, tenant_id: str | None, user_id: str | None) -> None:
        observed["tenant_id"] = tenant_id or ""
        observed["user_id"] = user_id or ""
        raise RuntimeError("sentinel")

    monkeypatch.setattr(helpers, "raise_rate_limit_http_error", fake_raise)

    quota = RateLimitQuota(
        name="signup_request_per_hour",
        limit=5,
        window_seconds=60,
        scope="ip",
    )

    with pytest.raises(RuntimeError):
        await helpers.apply_signup_quota(
            quota,
            key_parts=["client", "ua"],
            scope_value="client",
            policy="invite_only",
            flow="request",
            tenant_id="public-signup-request",
        )

    assert observed["tenant_id"] == "public-signup-request"
    assert observed["user_id"] == "client"


@pytest.mark.asyncio
async def test_apply_signup_quota_defaults_public_tenant(monkeypatch):
    limiter = _LimiterStub()
    monkeypatch.setattr(helpers, "rate_limiter", limiter)
    monkeypatch.setattr(helpers, "record_signup_blocked", lambda *, reason: None)
    monkeypatch.setattr(helpers, "record_signup_attempt", lambda *, result, policy: None)

    observed: dict[str, str] = {}

    def fake_raise(_: RateLimitExceeded, *, tenant_id: str | None, user_id: str | None) -> None:
        observed["tenant_id"] = tenant_id or ""
        observed["user_id"] = user_id or ""
        raise RuntimeError("sentinel")

    monkeypatch.setattr(helpers, "raise_rate_limit_http_error", fake_raise)

    quota = RateLimitQuota(
        name="signup_per_hour",
        limit=5,
        window_seconds=60,
        scope="ip",
    )

    with pytest.raises(RuntimeError):
        await helpers.apply_signup_quota(
            quota,
            key_parts=["client", "ua"],
            scope_value="client",
            policy="public",
            flow="register",
        )

    assert observed["tenant_id"] == helpers.DEFAULT_SIGNUP_TENANT_ID
    assert observed["user_id"] == "client"
