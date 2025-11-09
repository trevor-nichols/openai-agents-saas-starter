"""Authentication request and response models."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserLoginRequest(BaseModel):
    """Human user login payload."""

    email: EmailStr = Field(description="User email address.")
    password: str = Field(min_length=8, description="Plaintext password to verify.")
    tenant_id: str | None = Field(
        default=None,
        description="Tenant UUID when the user belongs to multiple tenants.",
    )


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
