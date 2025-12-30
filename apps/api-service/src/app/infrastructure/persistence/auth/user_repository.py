"""SQLAlchemy-backed user repository with Redis lockout helpers."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Protocol, cast

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.core.settings import Settings, get_settings
from app.domain.tenant_roles import TenantRole
from app.domain.users import (
    PasswordHistoryEntry,
    TenantMembershipDTO,
    UserCreatePayload,
    UserEmailConflictError,
    UserLoginEventDTO,
    UserProfilePatch,
    UserRecord,
    UserRepository,
    UserRepositoryError,
    UserStatus,
)
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.auth.models.membership import TenantUserMembership
from app.infrastructure.persistence.auth.models.user import (
    PasswordHistory,
    UserAccount,
    UserLoginEvent,
    UserProfile,
)
from app.infrastructure.persistence.auth.models.user import (
    UserStatus as DBUserStatus,
)
from app.infrastructure.redis.factory import get_redis_factory
from app.infrastructure.redis_types import RedisBytesClient

logger = logging.getLogger("api-service.persistence.users")


class LockoutStore(Protocol):
    async def increment(self, user_id: uuid.UUID, ttl_seconds: int) -> int: ...

    async def reset(self, user_id: uuid.UUID) -> None: ...

    async def lock(self, user_id: uuid.UUID, duration_seconds: int) -> None: ...

    async def unlock(self, user_id: uuid.UUID) -> None: ...

    async def is_locked(self, user_id: uuid.UUID) -> bool: ...


class NullLockoutStore:
    async def increment(self, _user_id: uuid.UUID, _ttl_seconds: int) -> int:
        return 0

    async def reset(self, _user_id: uuid.UUID) -> None:
        return None

    async def lock(self, _user_id: uuid.UUID, _duration_seconds: int) -> None:
        return None

    async def unlock(self, _user_id: uuid.UUID) -> None:
        return None

    async def is_locked(self, _user_id: uuid.UUID) -> bool:
        return False


class RedisLockoutStore:
    """Redis-backed counter and lock management for login attempts."""

    def __init__(self, client: RedisBytesClient, *, prefix: str = "auth:lockout") -> None:
        self._client = client
        self._prefix = prefix

    async def increment(self, user_id: uuid.UUID, ttl_seconds: int) -> int:
        key = self._counter_key(user_id)
        value = await self._client.incr(key)
        await self._client.expire(key, ttl_seconds)
        return int(value)

    async def reset(self, user_id: uuid.UUID) -> None:
        await self._client.delete(self._counter_key(user_id))

    async def lock(self, user_id: uuid.UUID, duration_seconds: int) -> None:
        await self._client.set(self._lock_key(user_id), b"1", ex=duration_seconds)

    async def unlock(self, user_id: uuid.UUID) -> None:
        await self._client.delete(self._lock_key(user_id))

    async def is_locked(self, user_id: uuid.UUID) -> bool:
        return bool(await self._client.exists(self._lock_key(user_id)))

    def _counter_key(self, user_id: uuid.UUID) -> str:
        return f"{self._prefix}:counter:{user_id}"

    def _lock_key(self, user_id: uuid.UUID) -> str:
        return f"{self._prefix}:state:{user_id}"


class PostgresUserRepository(UserRepository):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        lockout_store: LockoutStore,
    ) -> None:
        self._session_factory = session_factory
        self._lockout_store = lockout_store

    async def create_user(self, payload: UserCreatePayload) -> UserRecord:
        normalized_email = payload.email.lower().strip()
        user_id = payload.user_id or uuid.uuid4()
        async with self._session_factory() as session:
            try:
                user = UserAccount(
                    id=user_id,
                    email=normalized_email,
                    password_hash=payload.password_hash,
                    password_pepper_version=payload.password_pepper_version,
                    status=DBUserStatus(payload.status.value),
                    platform_role=payload.platform_role,
                )
                session.add(user)
                await session.flush()

                if payload.display_name:
                    profile = UserProfile(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        display_name=payload.display_name,
                    )
                    session.add(profile)

                if payload.tenant_id:
                    membership = TenantUserMembership(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        tenant_id=payload.tenant_id,
                        role=payload.role,
                    )
                    session.add(membership)

                session.add(
                    PasswordHistory(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        password_hash=payload.password_hash,
                        password_pepper_version=payload.password_pepper_version,
                    )
                )

                await session.commit()
            except IntegrityError as exc:  # pragma: no cover - handled via tests
                await session.rollback()
                raise UserRepositoryError(f"Failed to create user: {exc}") from exc

        record = await self.get_user_by_id(user_id)
        if record is None:
            raise UserRepositoryError("User creation succeeded but record could not be reloaded.")
        return record

    async def update_user_status(self, user_id: uuid.UUID, status: UserStatus) -> None:
        db_status = DBUserStatus(status.value)
        async with self._session_factory() as session:
            await session.execute(
                update(UserAccount)
                .where(UserAccount.id == user_id)
                .values(status=db_status, updated_at=datetime.now(UTC))
            )
            await session.commit()

    async def upsert_user_profile(
        self,
        user_id: uuid.UUID,
        update: UserProfilePatch,
        *,
        provided_fields: set[str],
    ) -> None:
        allowed_fields = {
            "display_name",
            "given_name",
            "family_name",
            "avatar_url",
            "timezone",
            "locale",
        }
        fields = [field for field in provided_fields if field in allowed_fields]
        if not fields:
            return
        async with self._session_factory() as session:
            profile = await session.scalar(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            if profile is None:
                profile = UserProfile(id=uuid.uuid4(), user_id=user_id)
                session.add(profile)

            for field in fields:
                setattr(profile, field, getattr(update, field))
            profile.updated_at = datetime.now(UTC)
            try:
                await session.commit()
            except IntegrityError as exc:  # pragma: no cover - defensive
                await session.rollback()
                raise UserRepositoryError("Failed to update user profile.") from exc

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        normalized = email.strip().lower()
        async with self._session_factory() as session:
            user = await self._fetch_user(session, email=normalized)
            if not user:
                return None
            return self._to_record(user)

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserRecord | None:
        async with self._session_factory() as session:
            user = await self._fetch_user(session, user_id=user_id)
            if not user:
                return None
            return self._to_record(user)

    async def update_user_email(self, user_id: uuid.UUID, new_email: str) -> None:
        normalized = new_email.strip().lower()
        now = datetime.now(UTC)
        async with self._session_factory() as session:
            try:
                await session.execute(
                    update(UserAccount)
                    .where(UserAccount.id == user_id)
                    .values(email=normalized, email_verified_at=None, updated_at=now)
                )
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise UserEmailConflictError("Email already registered.") from exc

    async def record_login_event(self, event: UserLoginEventDTO) -> None:
        async with self._session_factory() as session:
            row = UserLoginEvent(
                id=uuid.uuid4(),
                user_id=event.user_id,
                tenant_id=event.tenant_id,
                ip_hash=event.ip_hash,
                user_agent=event.user_agent,
                result=event.result,
                reason=event.reason,
                created_at=event.created_at,
            )
            session.add(row)
            await session.commit()

    async def list_password_history(
        self, user_id: uuid.UUID, limit: int = 5
    ) -> list[PasswordHistoryEntry]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PasswordHistory)
                .where(PasswordHistory.user_id == user_id)
                .order_by(PasswordHistory.created_at.desc())
                .limit(limit)
            )
            rows = result.scalars().all()
            return [
                PasswordHistoryEntry(
                    user_id=row.user_id,
                    password_hash=row.password_hash,
                    password_pepper_version=row.password_pepper_version,
                    created_at=row.created_at,
                )
                for row in rows
            ]

    async def add_password_history(self, entry: PasswordHistoryEntry) -> None:
        async with self._session_factory() as session:
            session.add(
                PasswordHistory(
                    id=uuid.uuid4(),
                    user_id=entry.user_id,
                    password_hash=entry.password_hash,
                    password_pepper_version=entry.password_pepper_version,
                    created_at=entry.created_at,
                )
            )
            await session.commit()

    async def trim_password_history(self, user_id: uuid.UUID, keep: int) -> None:
        if keep < 0:
            keep = 0
        async with self._session_factory() as session:
            if keep == 0:
                await session.execute(
                    delete(PasswordHistory).where(PasswordHistory.user_id == user_id)
                )
                await session.commit()
                return

            subquery = (
                select(PasswordHistory.id)
                .where(PasswordHistory.user_id == user_id)
                .order_by(PasswordHistory.created_at.desc())
                .offset(keep)
            )

            await session.execute(
                delete(PasswordHistory).where(PasswordHistory.id.in_(subquery))
            )
            await session.commit()

    async def update_password_hash(
        self,
        user_id: uuid.UUID,
        password_hash: str,
        *,
        password_pepper_version: str,
    ) -> None:
        now = datetime.now(UTC)
        async with self._session_factory() as session:
            await session.execute(
                update(UserAccount)
                .where(UserAccount.id == user_id)
                .values(
                    password_hash=password_hash,
                    password_pepper_version=password_pepper_version,
                    updated_at=now,
                )
            )
            session.add(
                PasswordHistory(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    password_hash=password_hash,
                    password_pepper_version=password_pepper_version,
                    created_at=now,
                )
            )
            await session.commit()

    async def increment_lockout_counter(self, user_id: uuid.UUID, *, ttl_seconds: int) -> int:
        return await self._lockout_store.increment(user_id, ttl_seconds)

    async def reset_lockout_counter(self, user_id: uuid.UUID) -> None:
        await self._lockout_store.reset(user_id)

    async def mark_user_locked(self, user_id: uuid.UUID, *, duration_seconds: int) -> None:
        await self._lockout_store.lock(user_id, duration_seconds)

    async def clear_user_lock(self, user_id: uuid.UUID) -> None:
        await self._lockout_store.unlock(user_id)

    async def is_user_locked(self, user_id: uuid.UUID) -> bool:
        return await self._lockout_store.is_locked(user_id)

    async def _fetch_user(
        self,
        session: AsyncSession,
        *,
        email: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> UserAccount | None:
        stmt = select(UserAccount).options(
            selectinload(UserAccount.memberships),
            selectinload(UserAccount.profile),
        )
        if email:
            stmt = stmt.where(UserAccount.email == email)
        if user_id:
            stmt = stmt.where(UserAccount.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    def _to_record(self, user: UserAccount) -> UserRecord:
        memberships = [
            TenantMembershipDTO(
                tenant_id=membership.tenant_id,
                role=membership.role,
                created_at=membership.created_at,
            )
            for membership in user.memberships
        ]
        display_name = user.profile.display_name if user.profile else None
        given_name = user.profile.given_name if user.profile else None
        family_name = user.profile.family_name if user.profile else None
        avatar_url = user.profile.avatar_url if user.profile else None
        timezone = user.profile.timezone if user.profile else None
        locale = user.profile.locale if user.profile else None
        raw_status = user.status.value if hasattr(user.status, "value") else str(user.status)
        status = UserStatus(raw_status)
        return UserRecord(
            id=user.id,
            email=user.email,
            status=status,
            password_hash=user.password_hash,
            password_pepper_version=user.password_pepper_version,
            created_at=user.created_at,
            updated_at=user.updated_at,
            display_name=display_name,
            given_name=given_name,
            family_name=family_name,
            avatar_url=avatar_url,
            timezone=timezone,
            locale=locale,
            memberships=memberships,
            email_verified_at=user.email_verified_at,
            platform_role=getattr(user, "platform_role", None),
        )

    async def mark_email_verified(self, user_id: uuid.UUID, *, timestamp: datetime) -> None:
        async with self._session_factory() as session:
            user = await session.get(UserAccount, user_id)
            if not user:
                return
            user.email_verified_at = timestamp
            if user.status == DBUserStatus.PENDING:
                user.status = DBUserStatus.ACTIVE
            user.updated_at = timestamp
            await session.commit()

    async def list_sole_owner_tenant_ids(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        owner_role = TenantRole.OWNER
        async with self._session_factory() as session:
            sole_owner_tenants = (
                select(TenantUserMembership.tenant_id)
                .where(TenantUserMembership.role == owner_role)
                .group_by(TenantUserMembership.tenant_id)
                .having(func.count(TenantUserMembership.user_id) == 1)
                .subquery()
            )
            stmt = select(TenantUserMembership.tenant_id).where(
                TenantUserMembership.user_id == user_id,
                TenantUserMembership.role == owner_role,
                TenantUserMembership.tenant_id.in_(select(sole_owner_tenants.c.tenant_id)),
            )
            result = await session.execute(stmt)
            return [row[0] for row in result.all()]


def build_lockout_store(settings: Settings) -> LockoutStore:
    redis_url = settings.resolve_auth_cache_redis_url()
    if not redis_url:
        raise RuntimeError(
            "AUTH_CACHE_REDIS_URL (or REDIS_URL) is required to build the lockout store."
        )
    client = cast(
        RedisBytesClient,
        get_redis_factory(settings).get_client("auth_cache"),
    )
    return RedisLockoutStore(client)


def get_user_repository(settings: Settings | None = None) -> UserRepository | None:
    settings = settings or get_settings()
    if not settings.database_url:
        return None
    try:
        session_factory = get_async_sessionmaker()
    except RuntimeError:
        return None
    lockout_store = build_lockout_store(settings)
    return PostgresUserRepository(session_factory, lockout_store)
