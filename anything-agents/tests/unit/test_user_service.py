"""Unit tests for the UserService domain logic."""

from __future__ import annotations

import asyncio
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

from app.core.config import Settings
from app.core.security import (
    LEGACY_PASSWORD_HASH_VERSION,
    PASSWORD_HASH_VERSION,
    pwd_context,
)
from app.domain.users import PasswordReuseError, UserCreate, UserCreatePayload, UserStatus
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
from app.services.user_service import (
    InvalidCredentialsError,
    IpThrottledError,
    MembershipNotFoundError,
    NullLoginThrottle,
    PasswordPolicyViolationError,
    UserLockedError,
    UserService,
)
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
def service_settings() -> Settings:
    settings = Settings()
    settings.auth_lockout_threshold = 2
    settings.auth_lockout_duration_minutes = 1 / 60  # 1 second
    settings.auth_lockout_window_minutes = 1 / 60
    return settings


@pytest.fixture
def lockout_redis() -> FakeRedis:
    return FakeRedis()


class _BlockingThrottle(NullLoginThrottle):
    def __init__(self) -> None:
        self.failures: list[str | None] = []
        self.blocked: set[str] = set()

    async def ensure_allowed(self, ip_address: str | None) -> None:
        if ip_address and ip_address in self.blocked:
            raise IpThrottledError("blocked")

    async def register_failure(self, ip_address: str | None) -> None:
        self.failures.append(ip_address)
        if ip_address:
            self.blocked.add(ip_address)


@pytest.fixture
async def user_service(
    session_factory: async_sessionmaker[AsyncSession],
    service_settings: Settings,
    lockout_redis: FakeRedis,
) -> UserService:
    store = RedisLockoutStore(lockout_redis)
    repository = PostgresUserRepository(session_factory, store)
    return UserService(repository, settings=service_settings, ip_throttler=NullLoginThrottle())


STRONG_PASSWORD = "VividOrchard!92Trail"
ALT_PASSWORD = "GraniteHarbor#713"


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
    await _register_user(user_service, tenant_id, "service@example.com", STRONG_PASSWORD)
    auth_user = await user_service.authenticate(
        email="service@example.com",
        password=STRONG_PASSWORD,
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
    await _register_user(user_service, tenant_id, "lock@example.com", "SummitValley*421")

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
    await _register_user(user_service, tenant_id, "unlock@example.com", "SilverGrove&884")

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
        password="SilverGrove&884",
        tenant_id=tenant_id,
        ip_address="2.2.2.2",
        user_agent="pytest",
    )
    assert auth_user.user_id is not None


@pytest.mark.asyncio
async def test_authenticate_migrates_legacy_hash(
    user_service: UserService,
    tenant_id,
) -> None:
    legacy_password = "LegacyPassword42!!"
    payload = UserCreatePayload(
        email="legacy@example.com",
        password_hash=pwd_context.hash(legacy_password),
        password_pepper_version=LEGACY_PASSWORD_HASH_VERSION,
        tenant_id=tenant_id,
        role="admin",
        display_name="Legacy",
        status=UserStatus.ACTIVE,
    )
    await user_service._repository.create_user(payload)

    auth_user = await user_service.authenticate(
        email="legacy@example.com",
        password=legacy_password,
        tenant_id=tenant_id,
        ip_address="3.3.3.3",
        user_agent="pytest",
    )
    assert auth_user.email == "legacy@example.com"

    refreshed = await user_service._repository.get_user_by_email("legacy@example.com")
    assert refreshed is not None
    assert refreshed.password_pepper_version == PASSWORD_HASH_VERSION


@pytest.mark.asyncio
async def test_change_password_updates_hash_and_enforces_history(
    user_service: UserService,
    tenant_id,
) -> None:
    await _register_user(user_service, tenant_id, "owner@example.com", STRONG_PASSWORD)
    user = await user_service._repository.get_user_by_email("owner@example.com")
    assert user is not None

    await user_service.change_password(
        user_id=user.id,
        current_password=STRONG_PASSWORD,
        new_password="SparrowMeadow??462",
    )

    refreshed = await user_service._repository.get_user_by_email("owner@example.com")
    assert refreshed is not None
    assert refreshed.password_hash != user.password_hash

    # Reusing an old password should be rejected.
    with pytest.raises(PasswordReuseError):
        await user_service.change_password(
            user_id=refreshed.id,
            current_password="SparrowMeadow??462",
            new_password=STRONG_PASSWORD,
        )


@pytest.mark.asyncio
async def test_change_password_rejects_weak_secret(
    user_service: UserService,
    tenant_id,
) -> None:
    await _register_user(user_service, tenant_id, "weak@example.com", STRONG_PASSWORD)
    user = await user_service._repository.get_user_by_email("weak@example.com")
    assert user is not None

    with pytest.raises(PasswordPolicyViolationError):
        await user_service.change_password(
            user_id=user.id,
            current_password=STRONG_PASSWORD,
            new_password="shortpass",
        )


@pytest.mark.asyncio
async def test_ip_throttle_blocks_after_failures(
    session_factory: async_sessionmaker[AsyncSession],
    service_settings: Settings,
    lockout_redis: FakeRedis,
    tenant_id,
) -> None:
    store = RedisLockoutStore(lockout_redis)
    repository = PostgresUserRepository(session_factory, store)
    throttle = _BlockingThrottle()
    service = UserService(repository, settings=service_settings, ip_throttler=throttle)

    await _register_user(service, tenant_id, "throttle@example.com", STRONG_PASSWORD)

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate(
            email="throttle@example.com",
            password="completely-wrong",
            tenant_id=tenant_id,
            ip_address="198.51.100.10",
            user_agent="pytest",
        )

    with pytest.raises(IpThrottledError):
        await service.authenticate(
            email="throttle@example.com",
            password=STRONG_PASSWORD,
            tenant_id=tenant_id,
            ip_address="198.51.100.10",
            user_agent="pytest",
        )


@pytest.mark.asyncio
async def test_admin_reset_password_validates_membership(
    user_service: UserService,
    tenant_id,
) -> None:
    await _register_user(user_service, tenant_id, "member@example.com", ALT_PASSWORD)
    user = await user_service._repository.get_user_by_email("member@example.com")
    assert user is not None

    await user_service.admin_reset_password(
        target_user_id=user.id,
        tenant_id=tenant_id,
        new_password="MarinerForest!!551",
    )

    auth_user = await user_service.authenticate(
        email="member@example.com",
        password="MarinerForest!!551",
        tenant_id=tenant_id,
        ip_address=None,
        user_agent=None,
    )
    assert auth_user.user_id == user.id

    other_tenant = uuid4()
    with pytest.raises(MembershipNotFoundError):
        await user_service.admin_reset_password(
            target_user_id=user.id,
            tenant_id=other_tenant,
            new_password="DoesNotMatter!!44",
        )
