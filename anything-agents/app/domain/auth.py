"""Domain models and contracts for authentication storage."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol
from uuid import UUID

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
    session_id: UUID | None = None

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

    async def list_service_account_tokens(
        self,
        *,
        tenant_ids: Sequence[str] | None,
        include_global: bool,
        account_query: str | None,
        fingerprint: str | None,
        status: ServiceAccountTokenStatus,
        limit: int,
        offset: int,
    ) -> ServiceAccountTokenListResult: ...


@dataclass(slots=True, frozen=True)
class SessionLocation:
    """Approximate geolocation data for a user session."""

    city: str | None = None
    region: str | None = None
    country: str | None = None


@dataclass(slots=True, frozen=True)
class SessionClientDetails:
    """Parsed metadata extracted from the user-agent string."""

    platform: str | None = None
    browser: str | None = None
    device: str | None = None


@dataclass(slots=True)
class UserSessionTokens:
    """Value object containing freshly minted access/refresh tokens."""

    access_token: str
    refresh_token: str
    expires_at: datetime
    refresh_expires_at: datetime
    kid: str
    refresh_kid: str
    scopes: list[str]
    tenant_id: str
    user_id: str
    email_verified: bool
    session_id: str
    token_type: str = "bearer"


@dataclass(slots=True, frozen=True)
class UserSession:
    """Persisted session/device metadata for a user."""

    id: UUID
    user_id: UUID
    tenant_id: UUID
    refresh_jti: str
    fingerprint: str | None
    ip_hash: str | None
    ip_masked: str | None
    user_agent: str | None
    client: SessionClientDetails
    location: SessionLocation | None
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime | None
    revoked_at: datetime | None


@dataclass(slots=True, frozen=True)
class UserSessionListResult:
    """Paginated session query result."""

    sessions: list[UserSession]
    total: int


class UserSessionRepository(Protocol):
    """Storage contract for device/session metadata."""

    async def upsert_session(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        tenant_id: UUID,
        refresh_jti: str,
        fingerprint: str | None,
        ip_address: str | None,
        user_agent: str | None,
        client: SessionClientDetails,
        location: SessionLocation | None,
        occurred_at: datetime,
    ) -> UserSession: ...

    async def list_sessions(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID | None = None,
        include_revoked: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> UserSessionListResult: ...

    async def get_session(self, *, session_id: UUID, user_id: UUID) -> UserSession | None: ...

    async def mark_session_revoked(
        self, *, session_id: UUID, reason: str | None = None
    ) -> bool: ...

    async def mark_session_revoked_by_jti(
        self, *, refresh_jti: str, reason: str | None = None
    ) -> bool: ...

    async def revoke_all_for_user(
        self, *, user_id: UUID, reason: str | None = None
    ) -> int: ...


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


class ServiceAccountTokenStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    ALL = "all"


@dataclass(slots=True, frozen=True)
class ServiceAccountTokenView:
    """Summary view of a stored service-account refresh token."""

    jti: str
    account: str
    tenant_id: str | None
    scopes: list[str]
    expires_at: datetime
    issued_at: datetime
    revoked_at: datetime | None
    revoked_reason: str | None
    fingerprint: str | None
    signing_kid: str


@dataclass(slots=True, frozen=True)
class ServiceAccountTokenListResult:
    """Paginated listing result for service-account tokens."""

    tokens: list[ServiceAccountTokenView]
    total: int
