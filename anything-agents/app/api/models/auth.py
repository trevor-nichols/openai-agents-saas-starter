"""Authentication request and response models."""

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT access token payload returned to clients."""

    access_token: str = Field(description="Signed JWT access token.")
    token_type: str = Field(
        default="bearer",
        description="Token type hint for the Authorization header.",
    )
    expires_in: int = Field(
        description="Token expiration time expressed in seconds.",
    )


class TokenData(BaseModel):
    """JWT claims used internally once a token is validated."""

    user_id: str = Field(description="Authenticated user identifier.")


class UserLogin(BaseModel):
    """User login credentials."""

    username: str = Field(description="Username or email.")
    password: str = Field(description="User password.")


class UserCreate(BaseModel):
    """User registration payload."""

    username: str = Field(
        min_length=3,
        max_length=50,
        description="Desired username.",
    )
    email: EmailStr = Field(description="User email address.")
    password: str = Field(
        min_length=8,
        description="Plaintext password to be hashed.",
    )


class UserResponse(BaseModel):
    """User payload returned by user-related endpoints."""

    id: str = Field(description="User identifier.")
    username: str = Field(description="Username.")
    email: str = Field(description="User email address.")
    is_active: bool = Field(description="Whether the user is active.")
    created_at: str = Field(description="Creation timestamp.")


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
