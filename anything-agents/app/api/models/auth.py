"""Authentication request and response models."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserLoginRequest(BaseModel):
    """Human user login payload."""

    email: EmailStr = Field(description="User email address.")
    password: str = Field(min_length=8, description="Plaintext password to verify.")
    tenant_id: str | None = Field(
        default=None,
        description="Tenant UUID when the user belongs to multiple tenants.",
    )


class UserRegisterRequest(BaseModel):
    """Public signup payload used to create a tenant + owner account."""

    email: EmailStr = Field(description="Primary user email used for login + billing.")
    password: str = Field(
        min_length=14,
        description="Password that meets the platform's minimum complexity requirements.",
    )
    tenant_name: str = Field(
        min_length=2,
        max_length=128,
        description="Display name for the tenant.",
    )
    display_name: str | None = Field(
        default=None, description="Optional profile display name for the owner account."
    )
    plan_code: str | None = Field(
        default=None,
        description="Requested billing plan (defaults to server configuration when omitted).",
    )
    trial_days: int | None = Field(
        default=None,
        ge=0,
        le=365,
        description=(
            "Optional trial duration hint; ignored unless the deployment explicitly "
            "allows overrides."
        ),
    )
    accept_terms: bool = Field(
        default=False,
        description="Indicates whether the caller accepted the Terms of Service.",
    )

    @field_validator("accept_terms")
    @classmethod
    def _require_terms(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Terms of Service must be accepted to create an account.")
        return value


class UserRefreshRequest(BaseModel):
    """Refresh session request payload."""

    refresh_token: str = Field(min_length=16, description="Previously issued refresh token.")


class UserSessionResponse(BaseModel):
    """Bearer credential pair returned after login or refresh."""

    access_token: str = Field(description="Signed JWT access token.")
    refresh_token: str = Field(description="Signed JWT refresh token.")
    token_type: str = Field(
        default="bearer",
        description="Token type hint for the Authorization header.",
    )
    expires_at: datetime = Field(description="ISO-8601 timestamp when the access token expires.")
    refresh_expires_at: datetime = Field(
        description="ISO-8601 timestamp when the refresh token expires."
    )
    kid: str = Field(description="Key identifier used to sign the access token.")
    refresh_kid: str = Field(description="Key identifier used to sign the refresh token.")
    scopes: list[str] = Field(description="Scopes granted to the session.")
    tenant_id: str = Field(description="Tenant identifier tied to the session.")
    user_id: str = Field(description="Authenticated user identifier.")


class UserRegisterResponse(UserSessionResponse):
    """Session response returned by /auth/register with tenant metadata."""

    tenant_slug: str = Field(description="URL-safe slug generated for the tenant.")


class ServiceAccountIssueRequest(BaseModel):
    """Request payload for service-account refresh token issuance."""

    account: str = Field(description="Service-account identifier.")
    scopes: list[str] = Field(description="Scopes requested for the service account.")
    tenant_id: str | None = Field(
        default=None,
        description="Tenant UUID when required by the service account.",
    )
    lifetime_minutes: int | None = Field(
        default=None,
        description="Optional refresh token lifetime in minutes.",
    )
    fingerprint: str | None = Field(
        default=None,
        description="Optional machine or pipeline identifier for auditing.",
    )
    force: bool = Field(
        default=False,
        description="Force new token creation even when an active token exists.",
    )


class ServiceAccountTokenResponse(BaseModel):
    """Response returned after issuing a service-account refresh token."""

    refresh_token: str = Field(description="Minted refresh token for the service account.")
    expires_at: str = Field(description="ISO-8601 expiration timestamp.")
    issued_at: str = Field(description="ISO-8601 issuance timestamp.")
    scopes: list[str] = Field(description="Authorized scopes.")
    tenant_id: str | None = Field(
        default=None,
        description="Tenant UUID if the account is tenant-scoped.",
    )
    kid: str = Field(description="Key identifier used to sign the token.")
    account: str = Field(description="Service-account identifier.")
    token_use: str = Field(description="Token classification (refresh, access, etc.).")
