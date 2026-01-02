"""Tenant seeding helpers."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.tenants.models import TenantAccount
from app.services.test_fixtures.schemas import FixtureTenant


async def ensure_tenant(session: AsyncSession, tenant_spec: FixtureTenant) -> TenantAccount:
    existing = await session.scalar(
        select(TenantAccount).where(TenantAccount.slug == tenant_spec.slug)
    )
    if existing:
        existing.name = tenant_spec.name
        return existing

    tenant = TenantAccount(id=uuid4(), slug=tenant_spec.slug, name=tenant_spec.name)
    session.add(tenant)
    # Explicit flush required because session autoflush is disabled; ensures FK targets exist.
    await session.flush()
    return tenant


__all__ = ["ensure_tenant"]
