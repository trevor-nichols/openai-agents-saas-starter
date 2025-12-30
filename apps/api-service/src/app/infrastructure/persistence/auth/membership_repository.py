"""Postgres repository for tenant membership operations."""

from __future__ import annotations

import uuid
from typing import Any, cast

from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings, get_settings
from app.domain.team import TeamMember, TeamMemberListResult, TenantMembershipRepository
from app.domain.tenant_roles import TenantRole
from app.domain.users import UserStatus
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.auth.models.membership import TenantUserMembership
from app.infrastructure.persistence.auth.models.user import UserAccount, UserProfile


class PostgresTenantMembershipRepository(TenantMembershipRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_members(
        self,
        *,
        tenant_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> TeamMemberListResult:
        async with self._session_factory() as session:
            total = await session.scalar(
                select(func.count())
                .select_from(TenantUserMembership)
                .where(TenantUserMembership.tenant_id == tenant_id)
            )
            owner_count = await session.scalar(
                select(func.count())
                .select_from(TenantUserMembership)
                .where(
                    TenantUserMembership.tenant_id == tenant_id,
                    TenantUserMembership.role == TenantRole.OWNER,
                )
            )
            stmt = (
                select(TenantUserMembership, UserAccount, UserProfile)
                .join(UserAccount, TenantUserMembership.user_id == UserAccount.id)
                .outerjoin(UserProfile, UserProfile.user_id == UserAccount.id)
                .where(TenantUserMembership.tenant_id == tenant_id)
                .order_by(UserAccount.email.asc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            members = [self._to_member(*row) for row in result.all()]

        return TeamMemberListResult(
            members=members,
            total=int(total or 0),
            owner_count=int(owner_count or 0),
        )

    async def get_member(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> TeamMember | None:
        async with self._session_factory() as session:
            stmt = (
                select(TenantUserMembership, UserAccount, UserProfile)
                .join(UserAccount, TenantUserMembership.user_id == UserAccount.id)
                .outerjoin(UserProfile, UserProfile.user_id == UserAccount.id)
                .where(
                    TenantUserMembership.tenant_id == tenant_id,
                    TenantUserMembership.user_id == user_id,
                )
            )
            row = (await session.execute(stmt)).first()
            if not row:
                return None
            return self._to_member(*row)

    async def add_member(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        role: TenantRole,
    ) -> TeamMember:
        async with self._session_factory() as session:
            membership = TenantUserMembership(
                id=uuid.uuid4(),
                user_id=user_id,
                tenant_id=tenant_id,
                role=role,
            )
            session.add(membership)
            await session.commit()

        member = await self.get_member(tenant_id=tenant_id, user_id=user_id)
        if member is None:
            raise RuntimeError("Failed to load newly added member.")
        return member

    async def update_role(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        role: TenantRole,
    ) -> TeamMember | None:
        async with self._session_factory() as session:
            result = await session.execute(
                update(TenantUserMembership)
                .where(
                    TenantUserMembership.tenant_id == tenant_id,
                    TenantUserMembership.user_id == user_id,
                )
                .values(role=role)
            )
            await session.commit()
            if int(cast(CursorResult[Any], result).rowcount or 0) == 0:
                return None

        return await self.get_member(tenant_id=tenant_id, user_id=user_id)

    async def remove_member(self, *, tenant_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        async with self._session_factory() as session:
            result = await session.execute(
                delete(TenantUserMembership).where(
                    TenantUserMembership.tenant_id == tenant_id,
                    TenantUserMembership.user_id == user_id,
                )
            )
            await session.commit()
            return bool(cast(CursorResult[Any], result).rowcount)

    async def membership_exists(self, *, tenant_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        async with self._session_factory() as session:
            value = await session.scalar(
                select(func.count())
                .select_from(TenantUserMembership)
                .where(
                    TenantUserMembership.tenant_id == tenant_id,
                    TenantUserMembership.user_id == user_id,
                )
            )
            return bool(value)

    async def count_members_by_role(self, *, tenant_id: uuid.UUID, role: TenantRole) -> int:
        async with self._session_factory() as session:
            value = await session.scalar(
                select(func.count())
                .select_from(TenantUserMembership)
                .where(
                    TenantUserMembership.tenant_id == tenant_id,
                    TenantUserMembership.role == role,
                )
            )
            return int(value or 0)

    @staticmethod
    def _to_member(
        membership: TenantUserMembership,
        user: UserAccount,
        profile: UserProfile | None,
    ) -> TeamMember:
        raw_status = user.status.value if hasattr(user.status, "value") else str(user.status)
        status = UserStatus(raw_status)
        return TeamMember(
            user_id=user.id,
            tenant_id=membership.tenant_id,
            email=user.email,
            display_name=profile.display_name if profile else None,
            role=membership.role,
            status=status,
            email_verified=user.email_verified_at is not None,
            joined_at=membership.created_at,
        )


def get_tenant_membership_repository(
    settings: Settings | None = None,
) -> TenantMembershipRepository | None:
    resolved_settings = settings or get_settings()
    if not resolved_settings.database_url:
        return None
    try:
        session_factory = get_async_sessionmaker()
    except RuntimeError:
        return None
    return PostgresTenantMembershipRepository(session_factory)


__all__ = ["PostgresTenantMembershipRepository", "get_tenant_membership_repository"]
