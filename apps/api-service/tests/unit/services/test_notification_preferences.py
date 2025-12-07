from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.infrastructure.persistence.auth.models import UserNotificationPreference
from app.infrastructure.persistence.models.base import Base
from app.services.notification_preferences import NotificationPreferenceService


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


@pytest.mark.asyncio
async def test_upsert_is_idempotent(session_factory: async_sessionmaker[AsyncSession]) -> None:
    svc = NotificationPreferenceService(session_factory)
    user_id = uuid4()
    tenant_id = uuid4()

    first = await svc.upsert_preference(
        user_id=user_id,
        tenant_id=tenant_id,
        channel="email",
        category="alerts",
        enabled=True,
    )
    second = await svc.upsert_preference(
        user_id=user_id,
        tenant_id=tenant_id,
        channel="email",
        category="alerts",
        enabled=False,
    )

    assert first.id == second.id
    assert second.enabled is False

    async with session_factory() as session:
        rows = (
            await session.execute(
                select(UserNotificationPreference).where(
                    UserNotificationPreference.user_id == user_id,
                    UserNotificationPreference.tenant_id == tenant_id,
                )
            )
        ).scalars().all()
        assert len(rows) == 1
        assert rows[0].enabled is False
