"""Shared helpers for translating rate-limit errors into HTTP responses."""

from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException, status

from app.observability.logging import log_event
from app.observability.metrics import record_rate_limit_hit
from app.services.shared.rate_limit_service import RateLimitExceeded


def raise_rate_limit_http_error(
    exc: RateLimitExceeded,
    *,
    tenant_id: str | None,
    user_id: str | None = None,
) -> NoReturn:
    """Log + emit metrics before surfacing a 429 response."""

    record_rate_limit_hit(quota=exc.quota, scope=exc.scope)
    log_event(
        "rate_limit.block",
        level="warning",
        quota=exc.quota,
        tenant_id=tenant_id or "unknown",
        user_id=user_id or "anonymous",
        limit=exc.limit,
        retry_after=exc.retry_after,
    )
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Rate limit exceeded ({exc.quota}). Retry after {exc.retry_after}s.",
        headers={"Retry-After": str(exc.retry_after)},
    ) from exc
