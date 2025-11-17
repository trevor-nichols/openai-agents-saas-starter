"""Shared helpers for signup-specific rate limit handling."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from app.api.dependencies import raise_rate_limit_http_error
from app.observability.metrics import record_signup_attempt, record_signup_blocked
from app.services.shared.rate_limit_service import RateLimitExceeded, RateLimitQuota, rate_limiter

DEFAULT_SIGNUP_TENANT_ID = "public-signup"


async def apply_signup_quota(
    quota: RateLimitQuota,
    *,
    key_parts: Sequence[str],
    scope_value: str,
    policy: str,
    flow: Literal["register", "request"],
    tenant_id: str = DEFAULT_SIGNUP_TENANT_ID,
) -> None:
    if quota.limit <= 0:
        return
    try:
        await rate_limiter.enforce(quota, list(key_parts))
    except RateLimitExceeded as exc:
        record_signup_blocked(reason=exc.quota)
        record_signup_attempt(result=f"{flow}_rate_limited", policy=policy)
        raise_rate_limit_http_error(exc, tenant_id=tenant_id, user_id=scope_value)
