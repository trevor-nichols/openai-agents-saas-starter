from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select

from app.infrastructure.persistence.auth.models import UserConsent
from app.infrastructure.persistence.models.base import Base
from app.services.consent_service import ConsentService


@pytest.fixture()
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_consent_record_is_idempotent(session_factory: async_sessionmaker[AsyncSession]) -> None:
    svc = ConsentService(session_factory)
    user_id = uuid4()

    first = await svc.record(user_id=user_id, policy_key="privacy", version="v1")
    second = await svc.record(user_id=user_id, policy_key="privacy", version="v1")

    assert first.id == second.id

    async with session_factory() as session:
        rows = (
            await session.execute(
                select(UserConsent).where(
                    UserConsent.user_id == user_id,
                    UserConsent.policy_key == "privacy",
                    UserConsent.version == "v1",
                )
            )
        ).scalars().all()
        assert len(rows) == 1
