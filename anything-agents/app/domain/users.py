"""Domain-level DTOs, records, and contracts for human users."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal, Protocol, Sequence
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


@dataclass(slots=True)
class PasswordHistoryEntry:
    user_id: UUID
    password_hash: str
    password_pepper_version: str
    created_at: datetime


@dataclass(slots=True)
class UserRecord:
    id: UUID
    email: EmailStr
    status: UserStatus
    password_hash: str
    password_pepper_version: str
    created_at: datetime
    updated_at: datetime
    display_name: str | None
    memberships: list[TenantMembershipDTO]


@dataclass(slots=True)
class UserCreatePayload:
    email: EmailStr
    password_hash: str
    password_pepper_version: str = "v1"
    status: UserStatus = UserStatus.ACTIVE
    tenant_id: UUID | None = None
    role: str = "member"
    display_name: str | None = None
    user_id: UUID | None = None


@dataclass(slots=True)
class AuthenticatedUser:
    user_id: UUID
    tenant_id: UUID
    email: EmailStr
    role: str
    scopes: list[str]


class UserRepository(Protocol):
    async def create_user(self, payload: UserCreatePayload) -> UserRecord:
        ...

    async def update_user_status(self, user_id: UUID, status: UserStatus) -> None:
        ...

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        ...

    async def get_user_by_id(self, user_id: UUID) -> UserRecord | None:
        ...

    async def record_login_event(self, event: UserLoginEventDTO) -> None:
        ...

    async def list_password_history(self, user_id: UUID, limit: int = 5) -> list[PasswordHistoryEntry]:
        ...

    async def add_password_history(self, entry: PasswordHistoryEntry) -> None:
        ...

    async def increment_lockout_counter(self, user_id: UUID, *, ttl_seconds: int) -> int:
        ...

    async def reset_lockout_counter(self, user_id: UUID) -> None:
        ...

    async def mark_user_locked(self, user_id: UUID, *, duration_seconds: int) -> None:
        ...

    async def clear_user_lock(self, user_id: UUID) -> None:
        ...

    async def is_user_locked(self, user_id: UUID) -> bool:
        ...


class UserRepositoryError(RuntimeError):
    """Base error for user repository operations."""


class UserNotFoundError(UserRepositoryError):
    """Raised when a user lookup fails."""


class PasswordReuseError(UserRepositoryError):
    """Raised when a new password matches recent history."""


__all__ = [
    "AuthenticatedUser",
    "PasswordHistoryEntry",
    "PasswordReuseError",
    "TenantMembershipDTO",
    "UserCreate",
    "UserCreatePayload",
    "UserLoginEventDTO",
    "UserRead",
    "UserRecord",
    "UserRepository",
    "UserRepositoryError",
    "UserStatus",
]
