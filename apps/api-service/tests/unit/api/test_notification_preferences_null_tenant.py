from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.auth.models import UserNotificationPreference
from app.infrastructure.persistence.models.base import Base
from app.services.notification_preferences import NotificationPreferenceService


@pytest.fixture()
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_global_notification_upsert_is_idempotent(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    svc = NotificationPreferenceService(session_factory)
    user_id = uuid4()

    await svc.upsert_preference(
        user_id=user_id,
        channel="email",
        category="alerts",
        enabled=True,
        tenant_id=None,
    )
    await svc.upsert_preference(
        user_id=user_id,
        channel="email",
        category="alerts",
        enabled=False,
        tenant_id=None,
    )

    async with session_factory() as session:
        rows = (
            await session.execute(
                select(UserNotificationPreference).where(
                    UserNotificationPreference.user_id == user_id,
                    UserNotificationPreference.tenant_id.is_(None),
                    UserNotificationPreference.channel == "email",
                    UserNotificationPreference.category == "alerts",
                )
            )
        ).scalars().all()
        assert len(rows) == 1
        assert rows[0].enabled is False
