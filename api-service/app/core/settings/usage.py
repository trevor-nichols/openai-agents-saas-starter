"""Settings related to usage guardrails and metering."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SoftLimitMode = Literal["warn", "block"]
UsageGuardrailCacheBackend = Literal["memory", "redis"]


class UsageGuardrailSettingsMixin(BaseModel):
    """Feature flags and tunables for plan-aware usage guardrails."""

    enable_usage_guardrails: bool = Field(
        default=False,
        alias="ENABLE_USAGE_GUARDRAILS",
        description=(
            "If true, enforce plan usage limits before servicing chat requests. "
            "Requires billing to be enabled."
        ),
    )
    usage_guardrail_cache_ttl_seconds: int = Field(
        default=30,
        alias="USAGE_GUARDRAIL_CACHE_TTL_SECONDS",
        ge=0,
        description=(
            "TTL for cached usage rollups (seconds). Set to 0 to disable caching."
        ),
    )
    usage_guardrail_cache_backend: UsageGuardrailCacheBackend = Field(
        default="redis",
        alias="USAGE_GUARDRAIL_CACHE_BACKEND",
        description="Cache backend for usage totals (`redis` or `memory`).",
    )
    usage_guardrail_soft_limit_mode: SoftLimitMode = Field(
        default="warn",
        alias="USAGE_GUARDRAIL_SOFT_LIMIT_MODE",
        description=(
            "How to react when soft limits are exceeded: 'warn' logs a warning but "
            "allows the request, while 'block' treats soft limits like hard caps."
        ),
    )


__all__ = [
    "UsageGuardrailSettingsMixin",
    "SoftLimitMode",
    "UsageGuardrailCacheBackend",
]
