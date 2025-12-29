"""Postgres repository for tenant account lookups."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings, get_settings
from app.domain.tenant_accounts import TenantAccountRepository
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.tenants.models import TenantAccount


class PostgresTenantAccountRepository(TenantAccountRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_name(self, tenant_id: UUID) -> str | None:
        async with self._session_factory() as session:
            return await session.scalar(
                select(TenantAccount.name).where(TenantAccount.id == tenant_id)
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
