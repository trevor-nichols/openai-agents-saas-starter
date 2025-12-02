from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.activity import ActivityEvent, ActivityEventFilters
from app.infrastructure.persistence.activity import models as _activity_models  # noqa: F401
from app.infrastructure.persistence.activity.repository import (
    SqlAlchemyActivityEventRepository,
)
from app.infrastructure.persistence.auth import models as _auth_models  # noqa: F401
from app.infrastructure.persistence.conversations.models import TenantAccount
from app.infrastructure.persistence.models.base import Base


@pytest.fixture(scope="module")
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


async def _seed_tenant(session_factory: async_sessionmaker[AsyncSession], tenant_id: str) -> None:
    async with session_factory() as session:
        session.add(
            TenantAccount(id=UUID(tenant_id), slug=f"tenant-{tenant_id[:8]}", name="Tenant")
        )
        await session.commit()


@pytest.mark.asyncio
async def test_list_events_paginates_and_orders(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_id = str(uuid4())
    await _seed_tenant(session_factory, tenant_id)
    repo = SqlAlchemyActivityEventRepository(session_factory)

    base = datetime(2024, 1, 1, tzinfo=UTC)
    events = [
        ActivityEvent(
            id=str(uuid4()),
            tenant_id=tenant_id,
            action="conversation.cleared",
            created_at=base + timedelta(seconds=2),
            metadata={"conversation_id": "c3"},
        ),
        ActivityEvent(
            id=str(uuid4()),
            tenant_id=tenant_id,
            action="conversation.cleared",
            created_at=base + timedelta(seconds=1),
            metadata={"conversation_id": "c2"},
        ),
        ActivityEvent(
            id=str(uuid4()),
            tenant_id=tenant_id,
            action="conversation.cleared",
            created_at=base + timedelta(seconds=1),
            metadata={"conversation_id": "c1"},
        ),
    ]
    for event in events:
        await repo.record(event)

    page1 = await repo.list_events(tenant_id, limit=2)
    ids_page1 = [item.id for item in page1.items]
    assert page1.items[0].id == events[0].id
    assert len(ids_page1) == 2
    assert page1.next_cursor is not None

    page2 = await repo.list_events(tenant_id, limit=2, cursor=page1.next_cursor)
    ids_page2 = [item.id for item in page2.items]
    assert len(ids_page2) == 1
    assert page2.next_cursor is None

    all_ids = set(ids_page1 + ids_page2)
    assert all_ids == {evt.id for evt in events}


@pytest.mark.asyncio
async def test_list_events_filters_and_isolates_tenants(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tenant_one = str(uuid4())
    tenant_two = str(uuid4())
    await _seed_tenant(session_factory, tenant_one)
    await _seed_tenant(session_factory, tenant_two)
    repo = SqlAlchemyActivityEventRepository(session_factory)

    target_actor = str(uuid4())
    target_request = "req-1"

    await repo.record(
        ActivityEvent(
            id=str(uuid4()),
            tenant_id=tenant_one,
            action="auth.login.success",
            created_at=datetime.now(tz=UTC),
            actor_id=target_actor,
            actor_type="user",
            object_type="session",
            object_id="sess-1",
            status="success",
            request_id=target_request,
            metadata={"user_id": target_actor},
        )
    )
    await repo.record(
        ActivityEvent(
            id=str(uuid4()),
            tenant_id=tenant_one,
            action="workflow.run.started",
            created_at=datetime.now(tz=UTC),
            actor_id=str(uuid4()),
            actor_type="user",
            object_type="workflow",
            object_id="wf-1",
            status="success",
            request_id="req-other",
            metadata={"workflow_key": "analysis"},
        )
    )
    await repo.record(
        ActivityEvent(
            id=str(uuid4()),
            tenant_id=tenant_two,
            action="auth.login.success",
            created_at=datetime.now(tz=UTC),
            actor_id=str(uuid4()),
            actor_type="user",
            object_type="session",
            object_id="sess-2",
            status="success",
        )
    )

    filters = ActivityEventFilters(
        action="auth.login.success",
        actor_id=target_actor,
        object_type="session",
        object_id="sess-1",
        status="success",
        request_id=target_request,
    )

    page = await repo.list_events(tenant_one, limit=10, filters=filters)

    assert len(page.items) == 1
    item = page.items[0]
    assert item.tenant_id == tenant_one
    assert item.actor_id == target_actor
    assert item.request_id == target_request

    # Tenant isolation: tenant_two records should never leak into tenant_one queries
    assert all(event.tenant_id == tenant_one for event in page.items)
