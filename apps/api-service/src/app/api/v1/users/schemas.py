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
    role: str = Field(description="Tenant role associated with the session.")
    email_verified: bool = Field(description="Whether the user's email is verified.")


class CurrentUserProfileSuccessResponse(SuccessResponse):
    data: CurrentUserProfileResponseData | None = Field(
        default=None,
        description="Current authenticated user profile payload.",
    )
