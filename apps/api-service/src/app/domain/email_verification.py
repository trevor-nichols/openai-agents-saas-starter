"""Domain models for email verification tokens."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(slots=True)
class EmailVerificationTokenRecord:
    token_id: str
    user_id: UUID
    email: str
    hashed_secret: str
    created_at: datetime
    expires_at: datetime
    fingerprint: str | None = None


class EmailVerificationTokenStore(Protocol):
    async def save(self, record: EmailVerificationTokenRecord, *, ttl_seconds: int) -> None: ...

    async def get(self, token_id: str) -> EmailVerificationTokenRecord | None: ...

    async def delete(self, token_id: str) -> None: ...


__all__ = [
    "EmailVerificationTokenRecord",
    "EmailVerificationTokenStore",
]
