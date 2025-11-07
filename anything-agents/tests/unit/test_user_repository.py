"""Unit tests for the PostgresUserRepository using an in-memory SQLite backend."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import EmailStr
from sqlalchemy.dialects.postgresql import CITEXT, JSONB, UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.domain.users import UserCreatePayload, UserLoginEventDTO, UserRecord, UserStatus
from app.infrastructure.persistence.auth.models import (
    PasswordHistory,
    TenantUserMembership,
    UserAccount,
    UserLoginEvent,
    UserProfile,
)
from app.infrastructure.persistence.auth.user_repository import (
    InMemoryLockoutStore,
    PostgresUserRepository,
)
from app.infrastructure.persistence.conversations.models import TenantAccount


@compiles(CITEXT, "sqlite")
def _compile_citext(element, compiler, **kwargs):  # pragma: no cover - dialect shim
    return "TEXT"


@compiles(PG_UUID, "sqlite")
def _compile_uuid(element, compiler, **kwargs):  # pragma: no cover - dialect shim
    return "TEXT"


@compiles(JSONB, "sqlite")
def _compile_jsonb(element, compiler, **kwargs):  # pragma: no cover - dialect shim
    return "TEXT"


def _create_core_tables(connection) -> None:
    tables = [
        TenantAccount.__table__,
        UserAccount.__table__,
        UserProfile.__table__,
        TenantUserMembership.__table__,
        PasswordHistory.__table__,
        UserLoginEvent.__table__,
    ]
    for table in tables:
        table.create(connection, checkfirst=True)


@pytest.fixture
async def session_factory() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(_create_core_tables)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def tenant_id(session_factory: async_sessionmaker[AsyncSession]):
    async with session_factory() as session:
        tenant = TenantAccount(id=uuid4(), slug="default", name="Default")
        session.add(tenant)
        await session.commit()
        return tenant.id


@pytest.fixture
async def repository(session_factory: async_sessionmaker[AsyncSession]) -> PostgresUserRepository:
    return PostgresUserRepository(session_factory, InMemoryLockoutStore())


async def _create_user(repo: PostgresUserRepository, tenant_id, email: str) -> UserRecord:
    payload = UserCreatePayload(
        email=email,
        password_hash="hashed",
        tenant_id=tenant_id,
        role="admin",
        display_name="Owner",
        status=UserStatus.ACTIVE,
    )
    return await repo.create_user(payload)


@pytest.mark.asyncio
async def test_create_and_fetch_user(repository: PostgresUserRepository, tenant_id) -> None:
    user = await _create_user(repository, tenant_id, "owner@example.com")
    assert user.display_name == "Owner"
    assert user.memberships and user.memberships[0].tenant_id == tenant_id

    fetched = await repository.get_user_by_email("owner@example.com")
    assert fetched is not None
    assert fetched.id == user.id


@pytest.mark.asyncio
async def test_lockout_counter_and_state(repository: PostgresUserRepository, tenant_id) -> None:
    user = await _create_user(repository, tenant_id, "lockout@example.com")
    count = await repository.increment_lockout_counter(user.id, ttl_seconds=5)
    assert count == 1
    await repository.mark_user_locked(user.id, duration_seconds=5)
    assert await repository.is_user_locked(user.id) is True
    await repository.clear_user_lock(user.id)
    assert await repository.is_user_locked(user.id) is False
    await repository.reset_lockout_counter(user.id)


@pytest.mark.asyncio
async def test_record_login_event(repository: PostgresUserRepository, tenant_id, session_factory: async_sessionmaker[AsyncSession]) -> None:
    user = await _create_user(repository, tenant_id, "events@example.com")
    event = UserLoginEventDTO(
        user_id=user.id,
        tenant_id=tenant_id,
        ip_hash="abcd",
        user_agent="pytest",
        result="success",
        reason="unit-test",
    )
    await repository.record_login_event(event)

    async with session_factory() as session:
        rows = await session.execute(UserLoginEvent.__table__.select())
        assert rows.first() is not None
