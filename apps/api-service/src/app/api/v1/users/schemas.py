"""Schemas for user profile endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.api.models.common import SuccessResponse


class CurrentUserProfileResponseData(BaseModel):
    user_id: str = Field(description="Current authenticated user id.")
    tenant_id: str = Field(description="Tenant id associated with the session.")
    email: EmailStr = Field(description="User email address.")
    display_name: str | None = Field(
        default=None,
        description="Preferred display name for the user, when available.",
    )
    given_name: str | None = Field(
        default=None,
        description="Optional given name for the user.",
    )
    family_name: str | None = Field(
        default=None,
        description="Optional family name for the user.",
    )
    avatar_url: str | None = Field(
        default=None,
        description="Optional avatar URL for the user.",
    )
    timezone: str | None = Field(
        default=None,
        description="Optional IANA timezone for the user.",
    )
    locale: str | None = Field(
        default=None,
        description="Optional locale for the user.",
    )
    role: str = Field(description="Tenant role associated with the session.")
    email_verified: bool = Field(description="Whether the user's email is verified.")


class CurrentUserProfileSuccessResponse(SuccessResponse):
    data: CurrentUserProfileResponseData | None = Field(
        default=None,
        description="Current authenticated user profile payload.",
    )


class UserProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    given_name: str | None = Field(default=None, min_length=1, max_length=64)
    family_name: str | None = Field(default=None, min_length=1, max_length=64)
    avatar_url: str | None = Field(default=None, min_length=1, max_length=512)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    locale: str | None = Field(default=None, min_length=1, max_length=32)


class UserEmailChangeRequest(BaseModel):
    current_password: str = Field(min_length=8, description="Current password for verification.")
    new_email: EmailStr = Field(description="Replacement email address.")


class UserEmailChangeResponseData(BaseModel):
    user_id: str = Field(description="Current authenticated user id.")
    email: EmailStr = Field(description="Updated email address.")
    email_verified: bool = Field(description="Whether the updated email is verified.")
    verification_sent: bool = Field(
        description="Whether a verification email was dispatched after the change."
    )


class UserEmailChangeSuccessResponse(SuccessResponse):
    data: UserEmailChangeResponseData | None = Field(
        default=None,
        description="Email change result payload.",
    )


class UserAccountDisableRequest(BaseModel):
    current_password: str = Field(min_length=8, description="Current password for verification.")


class UserAccountDisableResponseData(BaseModel):
    user_id: str = Field(description="Current authenticated user id.")
    disabled: bool = Field(description="Whether the account is now disabled.")
    revoked_sessions: int = Field(
        ge=0,
        description="Number of sessions revoked after disabling the account.",
    )


class UserAccountDisableSuccessResponse(SuccessResponse):
    data: UserAccountDisableResponseData | None = Field(
        default=None,
        description="Account disable result payload.",
    )
