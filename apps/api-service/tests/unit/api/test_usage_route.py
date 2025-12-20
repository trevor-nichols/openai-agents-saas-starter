from __future__ import annotations

import asyncio
from datetime import date
from sqlalchemy import select
from typing import AsyncGenerator, Generator
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.v1.usage.router import router as usage_router
import app.api.v1.usage.router as usage_module
from app.infrastructure.persistence.auth.models import UsageCounter, UsageCounterGranularity
from app.infrastructure.persistence.models.base import Base
from app.services.usage.counters import UsageCounterService


@pytest.fixture(scope="module")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine: AsyncEngine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.fixture()
async def seeded_usage(session_factory: async_sessionmaker[AsyncSession]) -> UUID:
    tenant_id = uuid4()
    async with session_factory() as session:
        row = UsageCounter(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=None,
            period_start=date.today(),
            granularity=UsageCounterGranularity.DAY,
            input_tokens=10,
            output_tokens=5,
            requests=2,
            storage_bytes=0,
        )
        session.add(row)
        await session.commit()
    return tenant_id


@pytest.fixture()
def client(session_factory: async_sessionmaker[AsyncSession], seeded_usage: UUID) -> TestClient:
    app = FastAPI()

    svc = UsageCounterService(session_factory)

    def _svc() -> UsageCounterService:  # pragma: no cover
        return svc

    from app.services.usage.counters import get_usage_counter_service

    dep = usage_router.routes[0].dependant.dependencies[0].call  # type: ignore[attr-defined]

    def _tenant_context():
        return TenantContext(tenant_id=str(seeded_usage), role=TenantRole.VIEWER, user={"user_id": "u"})

    app.dependency_overrides[dep] = _tenant_context
    usage_module.get_usage_counter_service = _svc
    app.include_router(usage_router, prefix="/api/v1")
    return TestClient(app)


def test_list_usage(client: TestClient) -> None:
    resp = client.get("/api/v1/usage")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["requests"] == 2
    assert data[0]["user_id"] is None


@pytest.mark.asyncio
async def test_increment_atomic(session_factory: async_sessionmaker[AsyncSession], seeded_usage: UUID) -> None:
    svc = UsageCounterService(session_factory)
    today = date.today()
    await svc.increment(
        tenant_id=seeded_usage,
        user_id=None,
        period_start=today,
        granularity=UsageCounterGranularity.DAY,
        input_tokens=5,
        output_tokens=7,
        requests=3,
    )
    async with session_factory() as session:
        rows = (
            await session.execute(select(UsageCounter).where(UsageCounter.tenant_id == seeded_usage))
        ).scalars().all()
        assert len(rows) == 1
        assert rows[0].input_tokens == 15  # 10 + 5
        assert rows[0].output_tokens == 12  # 5 + 7
        assert rows[0].requests == 5  # 2 + 3
        assert rows[0].user_id is None


@pytest.mark.asyncio
async def test_increment_tenant_null_user_upsert(session_factory: async_sessionmaker[AsyncSession]) -> None:
    svc = UsageCounterService(session_factory)
    tenant_id = uuid4()
    today = date.today()

    # first insert creates tenant-level bucket with user_id NULL
    await svc.increment(
        tenant_id=tenant_id,
        user_id=None,
        period_start=today,
        granularity=UsageCounterGranularity.DAY,
        requests=1,
    )
    # second insert should upsert same row, not violate FK/unique
    await svc.increment(
        tenant_id=tenant_id,
        user_id=None,
        period_start=today,
        granularity=UsageCounterGranularity.DAY,
        requests=2,
        input_tokens=100,
    )

    async with session_factory() as session:
        rows = (
            await session.execute(select(UsageCounter).where(UsageCounter.tenant_id == tenant_id))
        ).scalars().all()
        assert len(rows) == 1
        row = rows[0]
        assert row.user_id is None
        assert row.requests == 3  # 1 + 2
        assert row.input_tokens == 100
