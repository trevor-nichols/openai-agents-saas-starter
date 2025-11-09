"""Domain models and contracts for authentication storage."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from passlib.context import CryptContext


def make_scope_key(scopes: Sequence[str]) -> str:
    """Normalize scopes into a deterministic lookup key."""

    return " ".join(scopes)


@dataclass(slots=True, frozen=True)
class RefreshTokenRecord:
    """Represents a stored refresh token for service accounts or users."""

    token: str
    jti: str
    account: str
    tenant_id: str | None
    scopes: list[str]
    expires_at: datetime
    issued_at: datetime
    fingerprint: str | None = None
    signing_kid: str | None = None

    @property
    def scope_key(self) -> str:
        return make_scope_key(self.scopes)


class RefreshTokenRepository(Protocol):
    """Abstract storage contract for refresh tokens."""

    async def find_active(
        self, account: str, tenant_id: str | None, scopes: Sequence[str]
    ) -> RefreshTokenRecord | None: ...

    async def get_by_jti(self, jti: str) -> RefreshTokenRecord | None: ...

    async def save(self, record: RefreshTokenRecord) -> None: ...

    async def revoke(self, jti: str, *, reason: str | None = None) -> None: ...

    async def revoke_account(self, account: str, *, reason: str | None = None) -> int: ...


_REFRESH_TOKEN_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _pepperize(raw_token: str, pepper: str) -> str:
    if not pepper:
        raise ValueError("Refresh-token pepper must be configured.")
    return f"{pepper}:{raw_token}"


def hash_refresh_token(raw_token: str, *, pepper: str) -> str:
    """Hash a refresh token using bcrypt with an additional server-side pepper."""

    material = _pepperize(raw_token, pepper)
    return _REFRESH_TOKEN_CONTEXT.hash(material)


def verify_refresh_token(raw_token: str, hashed_token: str, *, pepper: str) -> bool:
    """Verify a raw refresh token against the stored hash."""

    material = _pepperize(raw_token, pepper)
    return _REFRESH_TOKEN_CONTEXT.verify(material, hashed_token)
