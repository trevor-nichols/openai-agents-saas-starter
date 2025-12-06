"""Operator-facing service that manages signup invites."""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.settings import Settings, get_settings
from app.domain.signup import (
    SignupInvite,
    SignupInviteCreate,
    SignupInviteListResult,
    SignupInviteRepository,
    SignupInviteReservation,
    SignupInviteStatus,
)
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.auth.signup_repository import (
    PostgresSignupInviteRepository,
)
from app.observability.logging import log_event


def _hash_token(token: str) -> str:
    normalized = token.strip()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest


def _token_hint(token: str) -> str:
    return token[:8]


@dataclass(slots=True)
class InviteIssueResult:
    invite: SignupInvite
    invite_token: str


@dataclass(slots=True)
class InviteReservationContext:
    invite: SignupInvite
    reservation: SignupInviteReservation
    _service: InviteService
    _finalized: bool = False
    _released: bool = False

    async def mark_succeeded(self, *, tenant_id: str | UUID, user_id: str | UUID) -> None:
        await self._service._finalize_reservation(
            reservation_id=self.reservation.id,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        self._finalized = True

    async def ensure_released(self, *, reason: str) -> None:
        if self._finalized or self._released:
            return
        await self._service._release_reservation(
            reservation_id=self.reservation.id,
            reason=reason,
        )
        self._released = True


class InviteServiceError(RuntimeError):
    """Base class for invite related failures."""


class InviteTokenRequiredError(InviteServiceError):
    """Raised when policy enforcement requires a token but one was not provided."""


class InviteNotFoundError(InviteServiceError):
    """Raised when a token cannot be resolved."""


class InviteRevokedError(InviteServiceError):
    """Raised when a token has been revoked or exhausted."""


class InviteExpiredError(InviteServiceError):
    """Raised when a token expired before redemption."""


class InviteEmailMismatchError(InviteServiceError):
    """Raised when a token is scoped to a different email address."""


class InviteRequestMismatchError(InviteServiceError):
    """Raised when approval-required flows try to reuse a request-less token."""


class InviteService:
    def __init__(
        self,
        *,
        repository: SignupInviteRepository | None = None,
        settings_factory: Callable[[], Settings] | None = None,
    ) -> None:
        self._repository = repository or PostgresSignupInviteRepository(get_async_sessionmaker())
        self._settings_factory = settings_factory or get_settings

    def set_repository(self, repository: SignupInviteRepository) -> None:
        self._repository = repository

    @property
    def repository(self) -> SignupInviteRepository:
        return self._repository

    async def issue_invite(
        self,
        *,
        issuer_user_id: str | UUID | None,
        issuer_tenant_id: str | UUID | None,
        invited_email: str | None,
        max_redemptions: int = 1,
        expires_in_hours: int | None = 72,
        note: str | None = None,
        signup_request_id: UUID | None = None,
    ) -> InviteIssueResult:
        if max_redemptions <= 0:
            raise ValueError("max_redemptions must be greater than zero")
        token = secrets.token_urlsafe(32)
        hashed = _hash_token(token)
        expires_at = (
            datetime.now(UTC) + timedelta(hours=expires_in_hours)
            if expires_in_hours
            else None
        )
        invite = await self.repository.create(
            SignupInviteCreate(
                token_hash=hashed,
                token_hint=_token_hint(token),
                invited_email=_normalize_email(invited_email),
                issuer_user_id=_normalize_uuid(issuer_user_id),
                issuer_tenant_id=_normalize_uuid(issuer_tenant_id),
                signup_request_id=signup_request_id,
                max_redemptions=max_redemptions,
                expires_at=expires_at,
                note=note,
                metadata=None,
            )
        )
        log_event(
            "signup.invite_issued",
            result="success",
            invite_id=str(invite.id),
            signup_request_id=str(signup_request_id) if signup_request_id else None,
        )
        return InviteIssueResult(invite=invite, invite_token=token)

    async def revoke_invite(self, invite_id: UUID, *, reason: str | None = None) -> SignupInvite:
        timestamp = datetime.now(UTC)
        record = await self.repository.mark_revoked(invite_id, timestamp=timestamp, reason=reason)
        if record is None:
            raise InviteNotFoundError("Invite not found or already revoked.")
        log_event("signup.invite_revoked", result="success", invite_id=str(invite_id))
        return record

    async def reserve_for_signup(
        self,
        *,
        token: str | None,
        email: str,
        require_request: bool,
    ) -> InviteReservationContext:
        invite = await self._resolve_invite(
            token,
            email=email,
            require_request=require_request,
        )
        now = datetime.now(UTC)
        ttl_seconds = self._get_reservation_ttl_seconds()
        expires_at = now + timedelta(seconds=ttl_seconds)
        reservation = await self.repository.reserve_invite(
            invite.id,
            email=email,
            now=now,
            expires_at=expires_at,
        )
        if reservation is None:
            raise InviteRevokedError("Invite token is no longer active.")
        log_event(
            "signup.invite_reserved",
            result="success",
            invite_id=str(invite.id),
            reservation_id=str(reservation.id),
            expires_at=expires_at.isoformat(),
        )
        return InviteReservationContext(invite=invite, reservation=reservation, _service=self)

    async def list_invites(
        self,
        *,
        status: SignupInviteStatus | None = None,
        email: str | None = None,
        signup_request_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SignupInviteListResult:
        return await self.repository.list_invites(
            status=status,
            email=_normalize_email(email),
            signup_request_id=signup_request_id,
            limit=limit,
            offset=offset,
        )

    async def get_invite(self, invite_id: UUID) -> SignupInvite | None:
        return await self.repository.get(invite_id)

    async def _resolve_invite(
        self,
        token: str | None,
        *,
        email: str,
        require_request: bool,
    ) -> SignupInvite:
        if not token:
            raise InviteTokenRequiredError("Invite token is required for signup.")
        hashed = _hash_token(token)
        invite = await self.repository.find_by_token_hash(hashed)
        if invite is None:
            raise InviteNotFoundError("Invite token is invalid.")
        now = datetime.now(UTC)
        if invite.status in (SignupInviteStatus.REVOKED, SignupInviteStatus.EXHAUSTED):
            raise InviteRevokedError("Invite token is no longer active.")
        if invite.expires_at and invite.expires_at <= now:
            await self.repository.mark_revoked(invite.id, timestamp=now, reason="expired")
            raise InviteExpiredError("Invite token has expired.")
        if invite.invited_email and invite.invited_email != _normalize_email(email):
            raise InviteEmailMismatchError("Invite token is restricted to a different email.")
        if require_request and invite.signup_request_id is None:
            raise InviteRequestMismatchError(
                "Approval-required signup must use an approved invite."
            )
        return invite

    async def _finalize_reservation(
        self,
        *,
        reservation_id: UUID,
        tenant_id: str | UUID,
        user_id: str | UUID,
    ) -> None:
        timestamp = datetime.now(UTC)
        tenant_uuid = _normalize_uuid(tenant_id)
        user_uuid = _normalize_uuid(user_id)
        if tenant_uuid is None or user_uuid is None:
            raise InviteServiceError("Invite reservation missing tenant or user context.")
        record = await self.repository.finalize_reservation(
            reservation_id,
            tenant_id=tenant_uuid,
            user_id=user_uuid,
            timestamp=timestamp,
        )
        if record is None:
            raise InviteServiceError("Invite reservation is no longer active.")
        log_event(
            "signup.invite_redeemed",
            result="success",
            invite_id=str(record.invite_id),
            reservation_id=str(record.id),
            tenant_id=str(record.tenant_id) if record.tenant_id else None,
        )

    async def _release_reservation(
        self,
        *,
        reservation_id: UUID,
        reason: str,
    ) -> None:
        timestamp = datetime.now(UTC)
        record = await self.repository.release_reservation(
            reservation_id,
            timestamp=timestamp,
            reason=reason,
        )
        if record is None:
            return
        log_event(
            "signup.invite_reservation_released",
            result="success",
            invite_id=str(record.invite_id),
            reservation_id=str(record.id),
            reason=reason,
        )

    def _get_reservation_ttl_seconds(self) -> int:
        settings = self._settings_factory()
        return max(60, settings.signup_invite_reservation_ttl_seconds)


def _normalize_email(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


def _normalize_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    cleaned = value.strip()
    if not cleaned:
        return None
    return UUID(cleaned)


def build_invite_service(
    *,
    repository: SignupInviteRepository | None = None,
    settings_factory: Callable[[], Settings] | None = None,
) -> InviteService:
    return InviteService(repository=repository, settings_factory=settings_factory)


def get_invite_service() -> InviteService:
    from app.bootstrap.container import get_container

    container = get_container()
    service = container.invite_service
    if service is None:
        repository = PostgresSignupInviteRepository(get_async_sessionmaker())
        container.invite_service = build_invite_service(repository=repository)
        service = container.invite_service
    assert service is not None  # narrow for type-checkers
    return service


__all__ = [
    "InviteExpiredError",
    "InviteIssueResult",
    "InviteNotFoundError",
    "InviteReservationContext",
    "InviteRequestMismatchError",
    "InviteRevokedError",
    "InviteService",
    "InviteServiceError",
    "InviteTokenRequiredError",
    "InviteEmailMismatchError",
    "build_invite_service",
    "get_invite_service",
]
