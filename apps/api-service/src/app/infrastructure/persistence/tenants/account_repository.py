"""Postgres repository for tenant account operations."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings, get_settings
from app.domain.tenant_accounts import (
    TenantAccount,
    TenantAccountCreate,
    TenantAccountListResult,
    TenantAccountRepository,
    TenantAccountSlugConflictError,
    TenantAccountStatus,
    TenantAccountStatusUpdate,
    TenantAccountUpdate,
)
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.models.base import UTC_NOW
from app.infrastructure.persistence.tenants.models import TenantAccount as ORMTenantAccount


class PostgresTenantAccountRepository(TenantAccountRepository):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        *,
        session: AsyncSession | None = None,
    ) -> None:
        if session is None and session_factory is None:
            raise RuntimeError("Either session_factory or session must be provided.")
        self._session_factory = session_factory
        self._session = session

    @classmethod
    def for_session(cls, session: AsyncSession) -> PostgresTenantAccountRepository:
        return cls(session_factory=None, session=session)

    @asynccontextmanager
    async def _session_scope(self) -> AsyncIterator[AsyncSession]:
        if self._session is not None:
            yield self._session
            return
        if self._session_factory is None:
            raise RuntimeError("Tenant account repository is missing a session factory.")
        async with self._session_factory() as session:
            yield session

    async def get(self, tenant_id: UUID) -> TenantAccount | None:
        async with self._session_scope() as session:
            record = await session.get(ORMTenantAccount, tenant_id)
            if record is None:
                return None
            return self._to_domain(record)

    async def get_by_slug(self, slug: str) -> TenantAccount | None:
        async with self._session_scope() as session:
            record = await session.scalar(
                select(ORMTenantAccount).where(ORMTenantAccount.slug == slug)
            )
            if record is None:
                return None
            return self._to_domain(record)

    async def get_name(self, tenant_id: UUID) -> str | None:
        async with self._session_scope() as session:
            return await session.scalar(
                select(ORMTenantAccount.name).where(ORMTenantAccount.id == tenant_id)
            )

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        status: TenantAccountStatus | None = None,
        query: str | None = None,
    ) -> TenantAccountListResult:
        filters = []
        if status is not None:
            filters.append(ORMTenantAccount.status == status)
        if query and query.strip():
            pattern = f"%{query.strip()}%"
            filters.append(
                or_(
                    ORMTenantAccount.name.ilike(pattern),
                    ORMTenantAccount.slug.ilike(pattern),
                )
            )

        async with self._session_scope() as session:
            total = await session.scalar(
                select(func.count()).select_from(ORMTenantAccount).where(*filters)
            )
            stmt = (
                select(ORMTenantAccount)
                .where(*filters)
                .order_by(ORMTenantAccount.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            rows = (await session.execute(stmt)).scalars().all()
            accounts = [self._to_domain(row) for row in rows]

        return TenantAccountListResult(accounts=accounts, total=int(total or 0))

    async def create(self, payload: TenantAccountCreate) -> TenantAccount:
        created_at = UTC_NOW()
        status_updated_at = UTC_NOW()
        suspended_at = (
            status_updated_at if payload.status == TenantAccountStatus.SUSPENDED else None
        )
        deprovisioned_at = (
            status_updated_at
            if payload.status == TenantAccountStatus.DEPROVISIONED
            else None
        )
        record = ORMTenantAccount(
            id=payload.account_id or uuid4(),
            slug=payload.slug,
            name=payload.name,
            status=payload.status,
            created_at=created_at,
            updated_at=created_at,
            status_updated_at=status_updated_at,
            status_updated_by=payload.status_updated_by,
            status_reason=payload.status_reason,
            suspended_at=suspended_at,
            deprovisioned_at=deprovisioned_at,
        )
        async with self._session_scope() as session:
            session.add(record)
            try:
                if self._session is None:
                    await session.commit()
                    await session.refresh(record)
                else:
                    await session.flush()
            except IntegrityError as exc:
                if self._session is None:
                    await session.rollback()
                raise TenantAccountSlugConflictError(
                    "Tenant slug already exists."
                ) from exc
            return self._to_domain(record)

    async def update(
        self, tenant_id: UUID, update: TenantAccountUpdate
    ) -> TenantAccount | None:
        async with self._session_scope() as session:
            record = await session.get(ORMTenantAccount, tenant_id)
            if record is None:
                return None
            if update.name is not None:
                record.name = update.name
            if update.slug is not None:
                record.slug = update.slug
            try:
                if self._session is None:
                    await session.commit()
                    await session.refresh(record)
                else:
                    await session.flush()
            except IntegrityError as exc:
                if self._session is None:
                    await session.rollback()
                raise TenantAccountSlugConflictError(
                    "Tenant slug already exists."
                ) from exc
            return self._to_domain(record)

    async def update_status(
        self, tenant_id: UUID, update: TenantAccountStatusUpdate
    ) -> TenantAccount | None:
        async with self._session_scope() as session:
            record = await session.get(ORMTenantAccount, tenant_id)
            if record is None:
                return None
            record.status = update.status
            record.status_updated_at = update.occurred_at
            record.status_updated_by = update.updated_by
            record.status_reason = update.reason
            if update.suspended_at is not None:
                record.suspended_at = update.suspended_at
            if update.deprovisioned_at is not None:
                record.deprovisioned_at = update.deprovisioned_at
            if self._session is None:
                await session.commit()
                await session.refresh(record)
            else:
                await session.flush()
            return self._to_domain(record)

    @staticmethod
    def _to_domain(record: ORMTenantAccount) -> TenantAccount:
        status = (
            record.status
            if isinstance(record.status, TenantAccountStatus)
            else TenantAccountStatus(str(record.status))
        )
        return TenantAccount(
            id=record.id,
            slug=record.slug,
            name=record.name,
            status=status,
            created_at=record.created_at,
            updated_at=record.updated_at,
            status_updated_at=record.status_updated_at,
            status_updated_by=record.status_updated_by,
            status_reason=record.status_reason,
            suspended_at=record.suspended_at,
            deprovisioned_at=record.deprovisioned_at,
        )


def get_tenant_account_repository(
    settings: Settings | None = None,
) -> TenantAccountRepository | None:
    resolved_settings = settings or get_settings()
    if not resolved_settings.database_url:
        return None
    try:
        session_factory = get_async_sessionmaker()
    except RuntimeError:
        return None
    return PostgresTenantAccountRepository(session_factory)


__all__ = ["PostgresTenantAccountRepository", "get_tenant_account_repository"]
