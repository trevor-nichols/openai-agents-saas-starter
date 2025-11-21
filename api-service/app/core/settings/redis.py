"""Redis fan-out settings."""
from __future__ import annotations

from pydantic import BaseModel, Field

from .utils import normalize_url


class RedisSettingsMixin(BaseModel):
    """Redis connection URLs for different workloads."""

    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    rate_limit_redis_url: str | None = Field(
        default=None,
        description="Redis URL dedicated to rate limiting (defaults to REDIS_URL when unset).",
        alias="RATE_LIMIT_REDIS_URL",
    )
    auth_cache_redis_url: str | None = Field(
        default=None,
        description="Redis URL dedicated to auth/session caches like refresh tokens and lockouts.",
        alias="AUTH_CACHE_REDIS_URL",
    )
    security_token_redis_url: str | None = Field(
        default=None,
        description=(
            "Redis URL dedicated to nonce/email/password token stores (falls back to REDIS_URL)."
        ),
        alias="SECURITY_TOKEN_REDIS_URL",
    )
    usage_guardrail_redis_url: str | None = Field(
        default=None,
        description="Redis URL dedicated to usage guardrail caches (defaults to REDIS_URL).",
        alias="USAGE_GUARDRAIL_REDIS_URL",
    )

    def resolve_rate_limit_redis_url(self) -> str | None:
        return normalize_url(self.rate_limit_redis_url) or normalize_url(self.redis_url)

    def resolve_auth_cache_redis_url(self) -> str | None:
        return normalize_url(self.auth_cache_redis_url) or normalize_url(self.redis_url)

    def resolve_security_token_redis_url(self) -> str | None:
        return normalize_url(self.security_token_redis_url) or normalize_url(self.redis_url)

    def resolve_usage_guardrail_redis_url(self) -> str | None:
        return normalize_url(self.usage_guardrail_redis_url) or normalize_url(self.redis_url)

    def require_hardened_redis(self) -> bool:
        guard = getattr(self, "should_enforce_secret_overrides", None)
        if callable(guard):
            result = guard()
            return bool(result)
        raise AttributeError(
            "RedisSettingsMixin requires SecuritySettingsMixin to supply secret enforcement"
        )
