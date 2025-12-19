"""Authentication request and response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.api.models.common import SuccessResponse
from app.core.password_policy import PasswordPolicyError, validate_password_strength


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
    invite_token: str | None = Field(
        default=None,
        description="Invite token or approval code required for invite-only deployments.",
    )

    @field_validator("accept_terms")
    @classmethod
    def _require_terms(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Terms of Service must be accepted to create an account.")
        return value

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str, info):
        inputs = []
        email = info.data.get("email") if hasattr(info, "data") and info.data else None
        if email:
            inputs.append(email)
        try:
            validate_password_strength(value, user_inputs=inputs)
        except PasswordPolicyError as exc:
            raise ValueError(str(exc)) from exc
        return value


class UserRefreshRequest(BaseModel):
    """Refresh session request payload."""

    refresh_token: str = Field(min_length=1, description="Previously issued refresh token.")


class PasswordForgotRequest(BaseModel):
    """Initiate a password reset email."""

    email: EmailStr = Field(description="Email address associated with the account.")


class PasswordResetConfirmRequest(BaseModel):
    """Redeem a password reset token to set a new password."""

    token: str = Field(min_length=1, description="Password reset token from email.")
    new_password: str = Field(
        min_length=14,
        description="Replacement password that satisfies platform policy.",
    )

    @field_validator("new_password")
    @classmethod
    def _validate_new_password(cls, value: str):
        try:
            validate_password_strength(value)
        except PasswordPolicyError as exc:
            raise ValueError(str(exc)) from exc
        return value


class UserLogoutRequest(BaseModel):
    """Payload for revoking a single refresh token."""

    refresh_token: str = Field(
        min_length=1,
        description="Refresh token to revoke for the current user.",
    )


class EmailVerificationConfirmRequest(BaseModel):
    """Payload for confirming the email verification token."""

    token: str = Field(min_length=1, description="Verification token delivered via email.")


class EmailVerificationStatusResponseData(BaseModel):
    email_verified: bool = Field(description="Whether the user's email address is verified.")


class EmailVerificationSendSuccessResponse(SuccessResponse):
    data: EmailVerificationStatusResponseData | None = Field(
        default=None,
        description="Email verification status payload.",
    )


class SessionLogoutResponseData(BaseModel):
    revoked: bool = Field(description="Whether the session/token was revoked by this request.")


class SessionLogoutAllResponseData(BaseModel):
    revoked: int = Field(
        ge=0,
        description="Number of sessions/tokens revoked by this request.",
    )


class LogoutSessionSuccessResponse(SuccessResponse):
    data: SessionLogoutResponseData | None = Field(
        default=None,
        description="Single-session logout result payload.",
    )


class LogoutAllSessionsSuccessResponse(SuccessResponse):
    data: SessionLogoutAllResponseData | None = Field(
        default=None,
        description="Logout-all result payload.",
    )


class SessionRevokeByIdSuccessResponse(SuccessResponse):
    data: SessionLogoutResponseData | None = Field(
        default=None,
        description="Session revocation result payload.",
    )


class CurrentUserInfoResponseData(BaseModel):
    user_id: str = Field(description="Current authenticated user id.")
    token_payload: dict[str, Any] = Field(description="Decoded access token claims.")


class CurrentUserInfoSuccessResponse(SuccessResponse):
    data: CurrentUserInfoResponseData | None = Field(
        default=None,
        description="Current authenticated user info payload.",
    )


class PasswordChangeRequest(BaseModel):
    """Self-service password change payload."""

    current_password: str = Field(
        min_length=8,
        description="Current password for verification.",
    )
    new_password: str = Field(
        min_length=14,
        description="New password that satisfies platform policy.",
    )


class PasswordResetRequest(BaseModel):
    """Admin-initiated password reset payload."""

    user_id: UUID = Field(description="Target user identifier.")
    new_password: str = Field(
        min_length=14,
        description="Replacement password that satisfies platform policy.",
    )


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
    scopes: list[str] = Field(description="Authorized scopes attached to the session.")
    tenant_id: str = Field(description="Tenant context associated with the tokens.")
    user_id: str = Field(description="User identifier encoded in the tokens.")
    email_verified: bool = Field(description="Whether the email has been verified.")
    session_id: UUID = Field(description="Opaque session identifier for device tracking.")


class SignupAccessPolicyResponse(BaseModel):
    policy: str = Field(description="Active signup access policy.")
    invite_required: bool = Field(description="Indicates whether an invite token is required.")
    request_access_enabled: bool = Field(
        description="Whether deployments expose the access-request workflow.")


class SignupInviteIssueRequest(BaseModel):
    invited_email: EmailStr | None = Field(
        default=None,
        description="Optional email restriction for the invite.",
    )
    max_redemptions: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Maximum number of tenants that can redeem the invite.",
    )
    expires_in_hours: int | None = Field(
        default=72,
        ge=1,
        le=24 * 14,
        description="Invite expiry window expressed in hours.",
    )
    note: str | None = Field(
        default=None,
        max_length=512,
        description="Operator note stored alongside the invite.",
    )
    signup_request_id: UUID | None = Field(
        default=None,
        description="Associate the invite with a previously submitted signup request.",
    )


class SignupInviteResponse(BaseModel):
    id: UUID
    token_hint: str
    invited_email: EmailStr | None = None
    status: str
    max_redemptions: int
    redeemed_count: int
    expires_at: datetime | None = None
    created_at: datetime
    signup_request_id: UUID | None = None
    note: str | None = None


class SignupInviteIssueResponse(SignupInviteResponse):
    invite_token: str = Field(description="Plaintext invite token (only returned once).")


class SignupInviteListResponse(BaseModel):
    invites: list[SignupInviteResponse]
    total: int


class SignupRequestPublicRequest(BaseModel):
    email: EmailStr
    organization: str = Field(min_length=2, max_length=128)
    full_name: str = Field(min_length=2, max_length=128)
    message: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional context describing the intended use case.",
    )
    accept_terms: bool = Field(description="Indicates that the requester accepted the Terms.")
    honeypot: str | None = Field(
        default=None,
        description="Hidden honeypot field used to detect basic bots.",
    )

    @field_validator("accept_terms")
    @classmethod
    def _confirm_terms(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Terms of Service must be accepted before requesting access.")
        return value


class SignupRequestResponse(BaseModel):
    id: UUID
    email: EmailStr
    organization: str | None
    full_name: str | None
    status: str
    created_at: datetime
    decision_reason: str | None = None
    invite_token_hint: str | None = None


class SignupRequestListResponse(BaseModel):
    requests: list[SignupRequestResponse]
    total: int


class SignupRequestApprovalRequest(BaseModel):
    note: str | None = Field(
        default=None,
        max_length=512,
        description="Optional note recorded alongside the invite and decision.",
    )
    invite_expires_in_hours: int | None = Field(
        default=72,
        ge=1,
        le=24 * 14,
        description="Optional invite expiry override in hours.",
    )


class SignupRequestRejectionRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=512,
        description="Reason communicated to operators when rejecting a request.",
    )


class SignupRequestDecisionResponse(BaseModel):
    request: SignupRequestResponse
    invite: SignupInviteIssueResponse | None = None


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


class BrowserServiceAccountIssueRequest(ServiceAccountIssueRequest):
    """Browser-initiated issuance request with justification."""

    reason: str = Field(
        min_length=10,
        max_length=512,
        description="Human-readable justification for auditing.",
    )


class ServiceAccountTokenResponse(BaseModel):
    """Response returned after issuing a service-account refresh token."""

    refresh_token: str = Field(description="Minted refresh token for the service account.")
    expires_at: str = Field(description="ISO-8601 expiration timestamp.")
    issued_at: str = Field(description="ISO-8601 issuance timestamp.")
    scopes: list[str] = Field(description="Authorized scopes attached to the token.")
    tenant_id: str | None = Field(
        default=None,
        description="Tenant UUID if the account is tenant-scoped.",
    )
    kid: str = Field(description="Key identifier used to sign the token.")
    account: str = Field(description="Service-account identifier.")
    token_use: str = Field(description="Token classification (refresh, access, etc.).")
    session_id: str | None = Field(
        default=None,
        description="Optional session identifier when linked to a human session.",
    )


class ServiceAccountTokenItem(BaseModel):
    """List view representation of a service-account refresh token."""

    jti: str = Field(description="Refresh token unique identifier (JWT jti).")
    account: str = Field(description="Service-account identifier owning the token.")
    tenant_id: str | None = Field(
        default=None, description="Tenant UUID when the token is tenant-scoped."
    )
    scopes: list[str] = Field(description="Authorized scopes.")
    issued_at: datetime = Field(description="Issuance timestamp.")
    expires_at: datetime = Field(description="Expiration timestamp.")
    revoked_at: datetime | None = Field(description="Revocation timestamp, if applicable.")
    revoked_reason: str | None = Field(
        default=None, description="Optional reason recorded during revocation."
    )
    fingerprint: str | None = Field(
        default=None, description="Caller-provided fingerprint for auditing."
    )
    signing_kid: str = Field(description="Key identifier used to sign the refresh token.")


class ServiceAccountTokenListResponse(BaseModel):
    """Paginated response for service-account token listings."""

    items: list[ServiceAccountTokenItem] = Field(description="Current page of results.")
    total: int = Field(description="Total number of matching tokens across all pages.")
    limit: int = Field(ge=1, le=100, description="Requested page size.")
    offset: int = Field(ge=0, description="Requested offset.")


class ServiceAccountTokenRevokeRequest(BaseModel):
    """Payload for revoking a service-account refresh token."""

    reason: str | None = Field(
        default=None,
        max_length=256,
        description="Human-readable explanation for auditing (required for operators).",
    )


class ServiceAccountTokenRevokeResponseData(BaseModel):
    jti: str = Field(description="Refresh token identifier (JWT jti).")


class ServiceAccountTokenRevokeSuccessResponse(SuccessResponse):
    data: ServiceAccountTokenRevokeResponseData | None = Field(
        default=None,
        description="Revoked token reference payload.",
    )


class SessionClientInfo(BaseModel):
    """Details about the client/browser reported for a session."""

    platform: str | None = Field(
        default=None,
        description="Operating system/platform hint derived from the user-agent.",
    )
    browser: str | None = Field(
        default=None,
        description="Browser family detected from the user-agent.",
    )
    device: str | None = Field(
        default=None,
        description="Device class (desktop, mobile, tablet, bot).",
    )
    user_agent: str | None = Field(
        default=None,
        description="Raw user-agent string captured during login/refresh.",
    )


class SessionLocationInfo(BaseModel):
    """Approximate geolocation information for a session."""

    city: str | None = Field(default=None, description="City derived from GeoIP (if available).")
    region: str | None = Field(default=None, description="Region/subdivision derived from GeoIP.")
    country: str | None = Field(default=None, description="Country code derived from GeoIP.")


class UserSessionItem(BaseModel):
    """Single session/device entry for session management UI."""

    id: UUID = Field(description="Session identifier.")
    tenant_id: UUID = Field(description="Tenant associated with the session.")
    created_at: datetime = Field(description="Timestamp when the session was first created.")
    last_seen_at: datetime | None = Field(description="Last activity timestamp for the session.")
    revoked_at: datetime | None = Field(description="When the session was revoked (if applicable).")
    ip_address_masked: str | None = Field(
        default=None, description="Masked IP address for user-facing audits."
    )
    fingerprint: str | None = Field(
        default=None,
        description="Server-generated fingerprint for the IP + user-agent combo.",
    )
    client: SessionClientInfo = Field(description="Client/browser metadata.")
    location: SessionLocationInfo | None = Field(
        default=None, description="Approximate location for the session."
    )
    current: bool = Field(description="True when this session matches the caller's token context.")


class UserSessionListResponse(BaseModel):
    """Paginated list of user sessions/devices."""

    sessions: list[UserSessionItem] = Field(description="Session records for the user.")
    total: int = Field(description="Total number of sessions matching the filter.")
    limit: int = Field(description="Maximum sessions returned in this response.")
    offset: int = Field(description="Offset applied when querying sessions.")
