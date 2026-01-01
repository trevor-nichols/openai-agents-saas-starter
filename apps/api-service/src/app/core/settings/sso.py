"""SSO/OIDC configuration knobs."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SsoSettingsMixin(BaseModel):
    sso_state_ttl_minutes: int = Field(
        default=10,
        description="TTL for SSO state/nonce/PKCE payloads in Redis (minutes).",
        alias="SSO_STATE_TTL_MINUTES",
    )
    sso_clock_skew_seconds: int = Field(
        default=60,
        description="Allowed clock skew when validating ID token timestamps (seconds).",
        alias="SSO_CLOCK_SKEW_SECONDS",
    )
    sso_client_secret_encryption_key: str | None = Field(
        default=None,
        description=(
            "Optional secret used to encrypt SSO client secrets at rest. "
            "Falls back to AUTH_SESSION_ENCRYPTION_KEY or SECRET_KEY when unset."
        ),
        alias="SSO_CLIENT_SECRET_ENCRYPTION_KEY",
    )


__all__ = ["SsoSettingsMixin"]
