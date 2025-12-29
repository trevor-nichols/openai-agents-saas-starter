"""Postgres repository for tenant member invites."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings, get_settings
from app.domain.team import (
    TeamInvite,
    TeamInviteCreate,
    TeamInviteListResult,
    TeamInviteRepository,
    TeamInviteStatus,
)
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.auth.models.team_invites import TenantMemberInvite


class PostgresTeamInviteRepository(TeamInviteRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, payload: TeamInviteCreate) -> TeamInvite:
        async with self._session_factory() as session:
            record = TenantMemberInvite(
                tenant_id=payload.tenant_id,
                token_hash=payload.token_hash,
                token_hint=payload.token_hint,
                invited_email=payload.invited_email,
                role=payload.role,
                created_by_user_id=payload.created_by_user_id,
                expires_at=payload.expires_at,
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return self._to_domain(record)

    async def get(self, invite_id: UUID) -> TeamInvite | None:
        async with self._session_factory() as session:
            record = await session.get(TenantMemberInvite, invite_id)
            if record is None:
                return None
            return self._to_domain(record)

    async def find_by_token_hash(self, token_hash: str) -> TeamInvite | None:
        async with self._session_factory() as session:
            stmt = select(TenantMemberInvite).where(
                TenantMemberInvite.token_hash == token_hash
            )
            record = (await session.execute(stmt)).scalar_one_or_none()
            if record is None:
                return None
            return self._to_domain(record)

    async def list_invites(
        self,
        *,
        tenant_id: UUID,
        status: TeamInviteStatus | None,
        email: str | None,
        limit: int,
        offset: int,
    ) -> TeamInviteListResult:
        async with self._session_factory() as session:
            filters: list[Any] = [TenantMemberInvite.tenant_id == tenant_id]
            if status is not None:
                filters.append(TenantMemberInvite.status == status)
            if email:
                filters.append(func.lower(TenantMemberInvite.invited_email) == email.lower())

            total_stmt = select(func.count()).select_from(TenantMemberInvite).where(*filters)
            total = await session.scalar(total_stmt)

            stmt = (
                select(TenantMemberInvite)
                .where(*filters)
                .order_by(TenantMemberInvite.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            rows = (await session.execute(stmt)).scalars().all()
            invites = [self._to_domain(row) for row in rows]

        return TeamInviteListResult(invites=invites, total=int(total or 0))

    async def mark_revoked(
        self,
        invite_id: UUID,
        *,
        tenant_id: UUID,
        timestamp: datetime,
        reason: str | None,
    ) -> TeamInvite | None:
        async with self._session_factory() as session:
            stmt = (
                update(TenantMemberInvite)
                .where(
                    TenantMemberInvite.id == invite_id,
                    TenantMemberInvite.tenant_id == tenant_id,
                    TenantMemberInvite.status == TeamInviteStatus.ACTIVE,
                )
                .values(
                    status=TeamInviteStatus.REVOKED,
                    revoked_at=timestamp,
                    revoked_reason=reason,
                    updated_at=timestamp,
                )
                .returning(TenantMemberInvite)
            )
            record = (await session.execute(stmt)).scalar_one_or_none()
            if record is None:
                await session.rollback()
                return None
            await session.commit()
            return self._to_domain(record)

    async def mark_accepted(
        self,
        invite_id: UUID,
        *,
        timestamp: datetime,
        accepted_by_user_id: UUID,
    ) -> TeamInvite | None:
        async with self._session_factory() as session:
            stmt = (
                update(TenantMemberInvite)
                .where(
                    TenantMemberInvite.id == invite_id,
                    TenantMemberInvite.status == TeamInviteStatus.ACTIVE,
                )
                .values(
                    status=TeamInviteStatus.ACCEPTED,
                    accepted_by_user_id=accepted_by_user_id,
                    accepted_at=timestamp,
                    updated_at=timestamp,
                )
                .returning(TenantMemberInvite)
            )
            record = (await session.execute(stmt)).scalar_one_or_none()
            if record is None:
                await session.rollback()
                return None
            await session.commit()
            return self._to_domain(record)

    async def mark_expired(self, invite_id: UUID, *, timestamp: datetime) -> TeamInvite | None:
        async with self._session_factory() as session:
            stmt = (
                update(TenantMemberInvite)
                .where(
                    TenantMemberInvite.id == invite_id,
                    TenantMemberInvite.status == TeamInviteStatus.ACTIVE,
                )
                .values(
                    status=TeamInviteStatus.EXPIRED,
                    revoked_at=timestamp,
                    revoked_reason="expired",
                    updated_at=timestamp,
                )
                .returning(TenantMemberInvite)
            )
            record = (await session.execute(stmt)).scalar_one_or_none()
            if record is None:
                await session.rollback()
                return None
            await session.commit()
            return self._to_domain(record)

    @staticmethod
    def _to_domain(record: TenantMemberInvite) -> TeamInvite:
        return TeamInvite(
            id=record.id,
            tenant_id=record.tenant_id,
            token_hash=record.token_hash,
            token_hint=record.token_hint,
            invited_email=record.invited_email,
            role=record.role,
            status=record.status,
            created_by_user_id=record.created_by_user_id,
            accepted_by_user_id=record.accepted_by_user_id,
            accepted_at=record.accepted_at,
            revoked_at=record.revoked_at,
            revoked_reason=record.revoked_reason,
            expires_at=record.expires_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


def get_team_invite_repository(
    settings: Settings | None = None,
) -> TeamInviteRepository | None:
    resolved_settings = settings or get_settings()
    if not resolved_settings.database_url:
        return None
    try:
        session_factory = get_async_sessionmaker()
    except RuntimeError:
        return None
    return PostgresTeamInviteRepository(session_factory)


__all__ = ["PostgresTeamInviteRepository", "get_team_invite_repository"]
