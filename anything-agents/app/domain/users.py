"""Domain-level DTOs and enums for human users."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class UserStatus(str, Enum):
    """Permitted lifecycle states for user accounts."""

    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"
    LOCKED = "locked"


class TenantMembershipDTO(BaseModel):
    tenant_id: UUID
    role: str = Field(min_length=1, max_length=32)
    created_at: datetime


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    memberships: list[TenantMembershipDTO] = Field(default_factory=list)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=14)
    tenant_id: UUID
    role: str = Field(default="admin", min_length=1, max_length=32)
    display_name: str | None = Field(default=None, max_length=128)

    @validator("password")
    def _validate_password_strength(cls, value: str) -> str:
        if value.lower() == value or value.upper() == value:
            raise ValueError("Password must mix character cases.")
        return value


class UserLoginEventDTO(BaseModel):
    user_id: UUID
    tenant_id: UUID | None = None
    ip_hash: str
    user_agent: str | None = None
    result: Literal["success", "failure", "locked"]
    reason: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


__all__ = [
    "TenantMembershipDTO",
    "UserCreate",
    "UserLoginEventDTO",
    "UserRead",
    "UserStatus",
]
