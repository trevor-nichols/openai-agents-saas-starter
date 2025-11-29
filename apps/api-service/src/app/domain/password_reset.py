"""Domain models for user password reset tokens."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(slots=True)
class PasswordResetTokenRecord:
    """Canonical representation of an issued password reset token."""

    token_id: str
    user_id: UUID
    email: str
    hashed_secret: str
    created_at: datetime
    expires_at: datetime
    fingerprint: str | None = None


class PasswordResetTokenStore(Protocol):
    """Abstract persistence contract for password reset tokens."""

    async def save(self, record: PasswordResetTokenRecord, *, ttl_seconds: int) -> None: ...

    async def get(self, token_id: str) -> PasswordResetTokenRecord | None: ...

    async def delete(self, token_id: str) -> None: ...


__all__ = [
    "PasswordResetTokenRecord",
    "PasswordResetTokenStore",
]
