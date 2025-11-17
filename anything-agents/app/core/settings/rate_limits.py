"""Rate limit configuration knobs."""
from __future__ import annotations

from pydantic import BaseModel, Field


class RateLimitSettingsMixin(BaseModel):
    chat_rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum chat completions allowed per user per minute.",
        alias="CHAT_RATE_LIMIT_PER_MINUTE",
    )
    chat_stream_rate_limit_per_minute: int = Field(
        default=30,
        description="Maximum streaming chat sessions started per user per minute.",
        alias="CHAT_STREAM_RATE_LIMIT_PER_MINUTE",
    )
    chat_stream_concurrent_limit: int = Field(
        default=5,
        description="Simultaneous streaming chat sessions allowed per user.",
        alias="CHAT_STREAM_CONCURRENT_LIMIT",
    )
    billing_stream_rate_limit_per_minute: int = Field(
        default=20,
        description="Maximum billing stream subscriptions allowed per tenant per minute.",
        alias="BILLING_STREAM_RATE_LIMIT_PER_MINUTE",
    )
    billing_stream_concurrent_limit: int = Field(
        default=3,
        description="Simultaneous billing stream connections allowed per tenant.",
        alias="BILLING_STREAM_CONCURRENT_LIMIT",
    )
    rate_limit_key_prefix: str = Field(
        default="rate-limit",
        description="Redis key namespace used by the rate limiter service.",
        alias="RATE_LIMIT_KEY_PREFIX",
    )
