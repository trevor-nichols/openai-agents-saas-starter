"""Postgres-backed repositories for signup invites and access requests."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.normalization import normalize_email
from app.domain.signup import (
    SignupInvite,
    SignupInviteCreate,
    SignupInviteListResult,
    SignupInviteRepository,
    SignupInviteReservation,
    SignupInviteReservationStatus,
    SignupInviteStatus,
    SignupRequest,
    SignupRequestCreate,
    SignupRequestListResult,
    SignupRequestRepository,
    SignupRequestStatus,
)
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.auth.models.signup import (
    TenantSignupInvite,
    TenantSignupInviteReservation,
    TenantSignupRequest,
)


class PostgresSignupInviteRepository(SignupInviteRepository):
    """Invite repository backed by tenant_signup_invites."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or get_async_sessionmaker()

    async def create(self, payload: SignupInviteCreate) -> SignupInvite:
        async with self._session_factory() as session:
            record = TenantSignupInvite(
                token_hash=payload.token_hash,
                token_hint=payload.token_hint,
                invited_email=payload.invited_email,
                issuer_user_id=payload.issuer_user_id,
                issuer_tenant_id=payload.issuer_tenant_id,
                signup_request_id=payload.signup_request_id,
                max_redemptions=payload.max_redemptions,
                expires_at=payload.expires_at,
                note=payload.note,
                metadata_json=payload.metadata,
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
        domain = self._to_domain(record)
        if domain is None:  # pragma: no cover - defensive
            raise RuntimeError("Failed to persist signup invite.")
        return domain

    async def get(self, invite_id: UUID) -> SignupInvite | None:
        async with self._session_factory() as session:
            record = await session.get(TenantSignupInvite, invite_id)
        return self._to_domain(record)

    async def find_by_token_hash(self, token_hash: str) -> SignupInvite | None:
        async with self._session_factory() as session:
            stmt = select(TenantSignupInvite).where(TenantSignupInvite.token_hash == token_hash)
            record = (await session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(record)

    async def mark_redeemed(self, invite_id: UUID, *, timestamp: datetime) -> SignupInvite | None:
        async with self._session_factory() as session:
            async with session.begin():
                stmt = (
                    select(TenantSignupInvite)
                    .where(TenantSignupInvite.id == invite_id)
                    .with_for_update()
                )
                record = (await session.execute(stmt)).scalar_one_or_none()
                if record is None:
                    return None
                if record.status != SignupInviteStatus.ACTIVE:
                    return None
                if record.expires_at and record.expires_at <= timestamp:
                    record.status = SignupInviteStatus.EXPIRED
                    record.updated_at = timestamp
                    return None
                record.redeemed_count += 1
                record.last_redeemed_at = timestamp
                record.updated_at = timestamp
                if record.redeemed_count >= record.max_redemptions:
                    record.status = SignupInviteStatus.EXHAUSTED
            await session.refresh(record)
        return self._to_domain(record)

    async def mark_revoked(
        self,
        invite_id: UUID,
        *,
        timestamp: datetime,
        reason: str | None,
    ) -> SignupInvite | None:
        async with self._session_factory() as session:
            async with session.begin():
                stmt = (
                    select(TenantSignupInvite)
                    .where(TenantSignupInvite.id == invite_id)
                    .with_for_update()
                )
                record = (await session.execute(stmt)).scalar_one_or_none()
                if record is None:
                    return None
                if record.status == SignupInviteStatus.REVOKED:
                    return self._to_domain(record)
                record.status = SignupInviteStatus.REVOKED
                record.revoked_at = timestamp
                record.revoked_reason = reason
                record.updated_at = timestamp
            await session.refresh(record)
        return self._to_domain(record)

    async def list_invites(
        self,
        *,
        status: SignupInviteStatus | None,
        email: str | None,
        signup_request_id: UUID | None,
        limit: int,
        offset: int,
    ) -> SignupInviteListResult:
        filters: list[Any] = []
        normalized_email = normalize_email(email)
        if status:
            filters.append(TenantSignupInvite.status == status)
        if normalized_email:
            filters.append(func.lower(TenantSignupInvite.invited_email) == normalized_email)
        if signup_request_id:
            filters.append(TenantSignupInvite.signup_request_id == signup_request_id)

        async with self._session_factory() as session:
            stmt = select(TenantSignupInvite).where(*filters).order_by(
                TenantSignupInvite.created_at.desc()
            )
            total_stmt = select(func.count()).select_from(TenantSignupInvite).where(*filters)
            total = int((await session.execute(total_stmt)).scalar_one())
            rows = (await session.execute(stmt.offset(offset).limit(limit))).scalars().all()
        invites = [invite for invite in (self._to_domain(row) for row in rows) if invite]
        return SignupInviteListResult(invites=invites, total=total)

    async def reserve_invite(
        self,
        invite_id: UUID,
        *,
        email: str,
        now: datetime,
        expires_at: datetime,
    ) -> SignupInviteReservation | None:
        normalized_email = normalize_email(email) or email
        async with self._session_factory() as session:
            async with session.begin():
                invite_stmt = (
                    select(TenantSignupInvite)
                    .where(TenantSignupInvite.id == invite_id)
                    .with_for_update()
                )
                invite = (await session.execute(invite_stmt)).scalar_one_or_none()
                if invite is None:
                    return None
                await self._expire_stale_reservations(session, invite_id, now)
                if invite.status != SignupInviteStatus.ACTIVE:
                    return None
                if invite.expires_at and invite.expires_at <= now:
                    invite.status = SignupInviteStatus.EXPIRED
                    invite.updated_at = now
                    return None
                active_stmt = (
                    select(func.count())
                    .select_from(TenantSignupInviteReservation)
                    .where(
                        TenantSignupInviteReservation.invite_id == invite_id,
                        TenantSignupInviteReservation.status
                        == SignupInviteReservationStatus.ACTIVE,
                    )
                )
                active_reservations = int((await session.execute(active_stmt)).scalar_one())
                remaining = invite.max_redemptions - invite.redeemed_count - active_reservations
                if remaining <= 0:
                    return None

                reservation = TenantSignupInviteReservation(
                    invite_id=invite_id,
                    email=normalized_email,
                    status=SignupInviteReservationStatus.ACTIVE,
                    reserved_at=now,
                    expires_at=expires_at,
                )
                session.add(reservation)
            await session.refresh(reservation)
        return self._reservation_to_domain(reservation)

    async def finalize_reservation(
        self,
        reservation_id: UUID,
        *,
        tenant_id: UUID,
        user_id: UUID,
        timestamp: datetime,
    ) -> SignupInviteReservation | None:
        async with self._session_factory() as session:
            async with session.begin():
                reservation_stmt = (
                    select(TenantSignupInviteReservation)
                    .where(TenantSignupInviteReservation.id == reservation_id)
                    .with_for_update()
                )
                reservation = (await session.execute(reservation_stmt)).scalar_one_or_none()
                if reservation is None:
                    return None
                invite_stmt = (
                    select(TenantSignupInvite)
                    .where(TenantSignupInvite.id == reservation.invite_id)
                    .with_for_update()
                )
                invite = (await session.execute(invite_stmt)).scalar_one_or_none()
                if invite is None:
                    return None
                if reservation.status != SignupInviteReservationStatus.ACTIVE:
                    return self._reservation_to_domain(reservation)
                if reservation.expires_at <= timestamp:
                    reservation.status = SignupInviteReservationStatus.EXPIRED
                    reservation.released_at = timestamp
                    reservation.released_reason = "reservation_expired"
                    reservation.updated_at = timestamp
                    return None

                reservation.status = SignupInviteReservationStatus.FINALIZED
                reservation.finalized_at = timestamp
                reservation.tenant_id = tenant_id
                reservation.user_id = user_id
                reservation.updated_at = timestamp

                invite.redeemed_count += 1
                invite.last_redeemed_at = timestamp
                invite.updated_at = timestamp
                if invite.redeemed_count >= invite.max_redemptions:
                    invite.status = SignupInviteStatus.EXHAUSTED
            await session.refresh(reservation)
        return self._reservation_to_domain(reservation)

    async def release_reservation(
        self,
        reservation_id: UUID,
        *,
        timestamp: datetime,
        reason: str | None,
    ) -> SignupInviteReservation | None:
        async with self._session_factory() as session:
            async with session.begin():
                reservation_stmt = (
                    select(TenantSignupInviteReservation)
                    .where(TenantSignupInviteReservation.id == reservation_id)
                    .with_for_update()
                )
                reservation = (await session.execute(reservation_stmt)).scalar_one_or_none()
                if reservation is None:
                    return None
                if reservation.status != SignupInviteReservationStatus.ACTIVE:
                    return self._reservation_to_domain(reservation)
                reservation.status = SignupInviteReservationStatus.RELEASED
                reservation.released_at = timestamp
                reservation.released_reason = reason
                reservation.updated_at = timestamp
            await session.refresh(reservation)
        return self._reservation_to_domain(reservation)

    @staticmethod
    def _to_domain(row: TenantSignupInvite | None) -> SignupInvite | None:
        if row is None:
            return None
        return SignupInvite(
            id=row.id,
            token_hash=row.token_hash,
            token_hint=row.token_hint,
            invited_email=row.invited_email,
            issuer_user_id=row.issuer_user_id,
            issuer_tenant_id=row.issuer_tenant_id,
            signup_request_id=row.signup_request_id,
            status=row.status,
            max_redemptions=row.max_redemptions,
            redeemed_count=row.redeemed_count,
            expires_at=row.expires_at,
            last_redeemed_at=row.last_redeemed_at,
            revoked_at=row.revoked_at,
            revoked_reason=row.revoked_reason,
            note=row.note,
            metadata=row.metadata_json,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _reservation_to_domain(
        row: TenantSignupInviteReservation | None,
    ) -> SignupInviteReservation | None:
        if row is None:
            return None
        return SignupInviteReservation(
            id=row.id,
            invite_id=row.invite_id,
            email=row.email,
            status=row.status,
            reserved_at=row.reserved_at,
            expires_at=row.expires_at,
            released_at=row.released_at,
            released_reason=row.released_reason,
            finalized_at=row.finalized_at,
            tenant_id=row.tenant_id,
            user_id=row.user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def _expire_stale_reservations(
        self,
        session: AsyncSession,
        invite_id: UUID,
        now: datetime,
    ) -> None:
        stmt = (
            select(TenantSignupInviteReservation)
            .where(
                TenantSignupInviteReservation.invite_id == invite_id,
                TenantSignupInviteReservation.status == SignupInviteReservationStatus.ACTIVE,
                TenantSignupInviteReservation.expires_at <= now,
            )
            .with_for_update(skip_locked=True)
        )
        rows = (await session.execute(stmt)).scalars().all()
        for row in rows:
            row.status = SignupInviteReservationStatus.EXPIRED
            row.released_at = now
            row.released_reason = "expired"
            row.updated_at = now


class PostgresSignupRequestRepository(SignupRequestRepository):
    """Repository for tenant_signup_requests."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or get_async_sessionmaker()

    async def create(self, payload: SignupRequestCreate) -> SignupRequest:
        async with self._session_factory() as session:
            record = TenantSignupRequest(
                email=payload.email,
                organization=payload.organization,
                full_name=payload.full_name,
                message=payload.message,
                ip_address=payload.ip_address,
                user_agent=payload.user_agent,
                honeypot_value=payload.honeypot_value,
                metadata_json=payload.metadata,
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
        domain = self._to_domain(record)
        if domain is None:  # pragma: no cover - defensive
            raise RuntimeError("Failed to persist signup request.")
        return domain

    async def get(self, request_id: UUID) -> SignupRequest | None:
        async with self._session_factory() as session:
            record = await session.get(TenantSignupRequest, request_id)
        return self._to_domain(record)

    async def list_requests(
        self,
        *,
        status: SignupRequestStatus | None,
        limit: int,
        offset: int,
    ) -> SignupRequestListResult:
        filters: list[Any] = []
        if status:
            filters.append(TenantSignupRequest.status == status)
        async with self._session_factory() as session:
            stmt = (
                select(TenantSignupRequest)
                .where(*filters)
                .order_by(TenantSignupRequest.created_at.desc())
            )
            total_stmt = select(func.count()).select_from(TenantSignupRequest).where(*filters)
            total = int((await session.execute(total_stmt)).scalar_one())
            rows = (await session.execute(stmt.offset(offset).limit(limit))).scalars().all()
        requests = [item for item in (self._to_domain(row) for row in rows) if item]
        return SignupRequestListResult(requests=requests, total=total)

    async def count_pending_requests_by_ip(self, ip_address: str) -> int:
        normalized = (ip_address or "").strip()
        if not normalized:
            return 0
        async with self._session_factory() as session:
            stmt = (
                select(func.count())
                .select_from(TenantSignupRequest)
                .where(
                    TenantSignupRequest.ip_address == normalized,
                    TenantSignupRequest.status == SignupRequestStatus.PENDING,
                )
            )
            return int((await session.execute(stmt)).scalar_one())

    async def transition_status(
        self,
        *,
        request_id: UUID,
        expected_status: SignupRequestStatus,
        new_status: SignupRequestStatus,
        decided_by: UUID,
        decided_at: datetime,
        decision_reason: str | None,
        invite_token_hint: str | None,
    ) -> SignupRequest | None:
        async with self._session_factory() as session:
            async with session.begin():
                stmt = (
                    select(TenantSignupRequest)
                    .where(
                        TenantSignupRequest.id == request_id,
                        TenantSignupRequest.status == expected_status,
                    )
                    .with_for_update()
                )
                record = (await session.execute(stmt)).scalar_one_or_none()
                if record is None:
                    return None
                record.status = new_status
                record.decided_by = decided_by
                record.decided_at = decided_at
                record.decision_reason = decision_reason
                record.invite_token_hint = invite_token_hint
                record.updated_at = decided_at
            await session.refresh(record)
        return self._to_domain(record)

    @staticmethod
    def _to_domain(row: TenantSignupRequest | None) -> SignupRequest | None:
        if row is None:
            return None
        return SignupRequest(
            id=row.id,
            email=row.email,
            organization=row.organization,
            full_name=row.full_name,
            message=row.message,
            status=row.status,
            decision_reason=row.decision_reason,
            decided_at=row.decided_at,
            decided_by=row.decided_by,
            signup_invite_token_hint=row.invite_token_hint,
            ip_address=row.ip_address,
            user_agent=row.user_agent,
            honeypot_value=row.honeypot_value,
            metadata=row.metadata_json,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


def get_signup_invite_repository() -> PostgresSignupInviteRepository:
    return PostgresSignupInviteRepository(get_async_sessionmaker())


def get_signup_request_repository() -> PostgresSignupRequestRepository:
    return PostgresSignupRequestRepository(get_async_sessionmaker())
