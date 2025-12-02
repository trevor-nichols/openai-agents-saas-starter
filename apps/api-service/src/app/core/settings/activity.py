"""Settings for activity/audit logging."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .utils import normalize_url


class ActivitySettingsMixin(BaseModel):
    enable_activity_stream: bool = Field(
        default=False,
        description="Enable Redis-backed SSE streaming for activity events.",
        alias="ENABLE_ACTIVITY_STREAM",
    )
    activity_events_redis_url: str | None = Field(
        default=None,
        description="Redis URL used for activity event streaming (defaults to REDIS_URL).",
        alias="ACTIVITY_EVENTS_REDIS_URL",
    )
    activity_stream_max_length: int = Field(
        default=2048,
        ge=128,
        description="Maximum Redis stream length for activity events per tenant.",
        alias="ACTIVITY_STREAM_MAX_LENGTH",
    )
    activity_stream_ttl_seconds: int = Field(
        default=86_400,
        ge=0,
        description="TTL applied to activity stream keys (0 disables TTL).",
        alias="ACTIVITY_STREAM_TTL_SECONDS",
    )

    def resolve_activity_events_redis_url(self) -> str | None:
        redis_source = getattr(self, "redis_url", None)
        return normalize_url(self.activity_events_redis_url) or normalize_url(redis_source)


__all__ = ["ActivitySettingsMixin"]
