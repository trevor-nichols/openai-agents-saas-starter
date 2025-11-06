"""Domain models and contracts for authentication storage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Sequence


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

    @property
    def scope_key(self) -> str:
        return make_scope_key(self.scopes)


class RefreshTokenRepository(Protocol):
    """Abstract storage contract for refresh tokens."""

    async def find_active(
        self, account: str, tenant_id: str | None, scopes: Sequence[str]
    ) -> RefreshTokenRecord | None:
        ...

    async def save(self, record: RefreshTokenRecord) -> None:
        ...

    async def revoke(self, jti: str, *, reason: str | None = None) -> None:
        ...
