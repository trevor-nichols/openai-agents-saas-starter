"""Unit tests for the PostgresUserRepository using an ephemeral SQLite backend."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast
from uuid import uuid4

import pytest
from fakeredis.aioredis import FakeRedis
from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import CITEXT, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.security import PASSWORD_HASH_VERSION
from app.domain.users import UserCreatePayload, UserLoginEventDTO, UserRecord, UserStatus
from app.infrastructure.persistence.auth.models import (
    PasswordHistory,
    TenantUserMembership,
    UserAccount,
    UserLoginEvent,
    UserProfile,
)
from app.infrastructure.persistence.auth.user_repository import (
    PostgresUserRepository,
    RedisLockoutStore,
)
from app.infrastructure.persistence.tenants.models import TenantAccount
from tests.utils.sqlalchemy import create_tables


@compiles(CITEXT, "sqlite")
def _compile_citext(element, compiler, **kwargs):  # pragma: no cover - dialect shim
    return "TEXT"


@compiles(PG_UUID, "sqlite")
def _compile_uuid(element, compiler, **kwargs):  # pragma: no cover - dialect shim
    return "TEXT"


@compiles(JSONB, "sqlite")
def _compile_jsonb(element, compiler, **kwargs):  # pragma: no cover - dialect shim
    return "TEXT"


AUTH_TABLES = cast(
    tuple[Table, ...],
    (
        TenantAccount.__table__,
        UserAccount.__table__,
        UserProfile.__table__,
        TenantUserMembership.__table__,
        PasswordHistory.__table__,
        UserLoginEvent.__table__,
    ),
)


def _create_core_tables(connection: Connection) -> None:
    create_tables(connection, AUTH_TABLES)


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(_create_core_tables)
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


@pytest.fixture
async def tenant_id(session_factory: async_sessionmaker[AsyncSession]):
    async with session_factory() as session:
        tenant = TenantAccount(id=uuid4(), slug="default", name="Default")
        session.add(tenant)
        await session.commit()
        return tenant.id


@pytest.fixture
def lockout_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
async def repository(
    session_factory: async_sessionmaker[AsyncSession],
    lockout_redis: FakeRedis,
) -> PostgresUserRepository:
    store = RedisLockoutStore(lockout_redis)
    return PostgresUserRepository(session_factory, store)


async def _create_user(repo: PostgresUserRepository, tenant_id, email: str) -> UserRecord:
    payload = UserCreatePayload(
        email=email,
        password_hash="hashed",
        password_pepper_version=PASSWORD_HASH_VERSION,
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
async def test_record_login_event(
    repository: PostgresUserRepository, tenant_id, session_factory: async_sessionmaker[AsyncSession]
) -> None:
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


@pytest.mark.asyncio
async def test_update_password_hash(
    repository: PostgresUserRepository,
    tenant_id,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user = await _create_user(repository, tenant_id, "rotate@example.com")

    await repository.update_password_hash(
        user.id,
        password_hash="repeppered",
        password_pepper_version=PASSWORD_HASH_VERSION,
    )

    refreshed = await repository.get_user_by_id(user.id)
    assert refreshed is not None
    assert refreshed.password_hash == "repeppered"
    assert refreshed.password_pepper_version == PASSWORD_HASH_VERSION

    async with session_factory() as session:
        rows = await session.execute(
            PasswordHistory.__table__
            .select()
            .where(PasswordHistory.__table__.c.user_id == user.id)
        )
        history_rows = rows.fetchall()
        assert len(history_rows) == 2


@pytest.mark.asyncio
async def test_trim_password_history_keeps_most_recent(
    repository: PostgresUserRepository,
    tenant_id,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user = await _create_user(repository, tenant_id, "history@example.com")

    for idx in range(4):
        await repository.update_password_hash(
            user.id,
            password_hash=f"hash-{idx}",
            password_pepper_version=PASSWORD_HASH_VERSION,
        )

    await repository.trim_password_history(user.id, keep=2)

    async with session_factory() as session:
        rows = await session.execute(
            PasswordHistory.__table__
            .select()
            .where(PasswordHistory.__table__.c.user_id == user.id)
            .order_by(PasswordHistory.__table__.c.created_at.desc())
        )
        history_rows = rows.fetchall()

    assert len(history_rows) == 2
    assert history_rows[0].password_hash == "hash-3"
    assert history_rows[1].password_hash == "hash-2"
