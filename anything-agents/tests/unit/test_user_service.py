"""Unit tests for the UserService domain logic."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from fakeredis.aioredis import FakeRedis
from sqlalchemy.dialects.postgresql import CITEXT, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.config import Settings
from app.domain.users import UserCreate
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
from app.infrastructure.persistence.conversations.models import TenantAccount
from app.services.user_service import InvalidCredentialsError, UserLockedError, UserService


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
def service_settings() -> Settings:
    settings = Settings()
    settings.auth_lockout_threshold = 2
    settings.auth_lockout_duration_minutes = 1 / 60  # 1 second
    settings.auth_lockout_window_minutes = 1 / 60
    return settings


@pytest.fixture
def lockout_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
async def user_service(
    session_factory: async_sessionmaker[AsyncSession],
    service_settings: Settings,
    lockout_redis: FakeRedis,
) -> UserService:
    store = RedisLockoutStore(lockout_redis)
    repository = PostgresUserRepository(session_factory, store)
    return UserService(repository, settings=service_settings)


async def _register_user(service: UserService, tenant_id, email: str, password: str) -> None:
    create_payload = UserCreate(
        email=email,
        password=password,
        tenant_id=tenant_id,
        role="admin",
        display_name="Owner",
    )
    await service.register_user(create_payload)


@pytest.mark.asyncio
async def test_authenticate_success(user_service: UserService, tenant_id) -> None:
    await _register_user(user_service, tenant_id, "service@example.com", "Str0ngPassword!!")
    auth_user = await user_service.authenticate(
        email="service@example.com",
        password="Str0ngPassword!!",
        tenant_id=tenant_id,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    assert auth_user.email == "service@example.com"
    assert "conversations:read" in auth_user.scopes


@pytest.mark.asyncio
async def test_authenticate_invalid_password_leads_to_lockout(
    user_service: UserService, tenant_id
) -> None:
    await _register_user(user_service, tenant_id, "lock@example.com", "AnotherStrongPass!!")

    with pytest.raises(InvalidCredentialsError):
        await user_service.authenticate(
            email="lock@example.com",
            password="wrongpass",
            tenant_id=tenant_id,
            ip_address="1.1.1.1",
            user_agent="pytest",
        )

    with pytest.raises(UserLockedError):
        await user_service.authenticate(
            email="lock@example.com",
            password="wrongpass",
            tenant_id=tenant_id,
            ip_address="1.1.1.1",
            user_agent="pytest",
        )


@pytest.mark.asyncio
async def test_locked_user_unlocks_after_duration(
    user_service: UserService,
    tenant_id,
) -> None:
    await _register_user(user_service, tenant_id, "unlock@example.com", "Password1234!!")

    # Trip lockout
    for _ in range(2):
        with pytest.raises((InvalidCredentialsError, UserLockedError)):
            await user_service.authenticate(
                email="unlock@example.com",
                password="bad-password",
                tenant_id=tenant_id,
                ip_address="2.2.2.2",
                user_agent="pytest",
            )

    await asyncio.sleep(1.1)  # wait just over the 1 second lockout duration

    auth_user = await user_service.authenticate(
        email="unlock@example.com",
        password="Password1234!!",
        tenant_id=tenant_id,
        ip_address="2.2.2.2",
        user_agent="pytest",
    )
    assert auth_user.user_id is not None
