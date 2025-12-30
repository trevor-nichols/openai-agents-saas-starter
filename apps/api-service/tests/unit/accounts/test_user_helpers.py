"""Unit tests for modular user-service helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fakeredis.aioredis import FakeRedis

from app.core.security import get_password_hash
from app.core.settings import Settings
from app.domain.tenant_roles import TenantRole
from app.domain.users import (
    PasswordHistoryEntry,
    TenantMembershipDTO,
    UserLoginEventDTO,
    UserRecord,
    UserStatus,
    UserRepository,
)
from app.services.users import (
    IpThrottledError,
    MembershipNotFoundError,
    PasswordReuseError,
    TenantContextRequiredError,
    UserLockedError,
)
from app.services.users.factory import build_user_service
from app.services.users.lockout import LockoutManager
from app.services.users.login_events import ActivityRecorder, LoginEventRecorder
from app.services.users.membership import resolve_membership
from app.services.users.passwords import PasswordPolicyManager
from app.services.users.scopes import scopes_for_role
from app.services.users.throttling import NullLoginThrottle, RedisLoginThrottle


class _RecordingActivity(ActivityRecorder):
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def record(
        self,
        *,
        tenant_id: str,
        action: str,
        actor_id: str | None = None,
        actor_type: str | None = None,
        status: str = "success",
        source: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "action": action,
                "actor_id": actor_id,
                "status": status,
                "metadata": dict(metadata or {}),
            }
        )


class _LoginEventRepo:
    def __init__(self) -> None:
        self.events: list[UserLoginEventDTO] = []

    async def record_login_event(self, event) -> None:  # pragma: no cover - simple collector
        self.events.append(event)


class _PasswordRepo:
    def __init__(self) -> None:
        self.history: list[PasswordHistoryEntry] = []
        self.trim_calls: list[int] = []

    async def list_password_history(self, user_id: UUID, limit: int = 5):
        return self.history[:limit]

    async def trim_password_history(self, user_id: UUID, keep: int) -> None:
        self.trim_calls.append(keep)


class _LockoutRepo:
    def __init__(self) -> None:
        self.failures = 0
        self.status: dict[UUID, UserStatus] = {}
        self.locked: set[UUID] = set()

    async def increment_lockout_counter(self, user_id: UUID, *, ttl_seconds: int) -> int:
        self.failures += 1
        return self.failures

    async def update_user_status(self, user_id: UUID, status: UserStatus) -> None:
        self.status[user_id] = status

    async def mark_user_locked(self, user_id: UUID, *, duration_seconds: int) -> None:
        self.locked.add(user_id)

    async def is_user_locked(self, user_id: UUID) -> bool:
        return user_id in self.locked

    async def reset_lockout_counter(self, user_id: UUID) -> None:
        self.failures = 0

    async def clear_user_lock(self, user_id: UUID) -> None:
        self.locked.discard(user_id)


def _user_record(user_id: UUID | None = None) -> UserRecord:
    uid = user_id or uuid4()
    membership = TenantMembershipDTO(
        tenant_id=uuid4(), role=TenantRole.ADMIN, created_at=datetime.now(UTC)
    )
    return UserRecord(
        id=uid,
        email="u@example.com",
        status=UserStatus.ACTIVE,
        password_hash=get_password_hash("Passw0rd!Passw0rd!"),
        password_pepper_version="v2",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        display_name=None,
        given_name=None,
        family_name=None,
        avatar_url=None,
        timezone=None,
        locale=None,
        memberships=[membership],
        email_verified_at=None,
        platform_role=None,
    )


@pytest.mark.asyncio
async def test_login_event_recorder_invokes_activity_recorder() -> None:
    repo = _LoginEventRepo()
    activity = _RecordingActivity()
    recorder = LoginEventRecorder(cast(UserRepository, repo), activity_recorder=activity)
    uid, tid = uuid4(), uuid4()

    await recorder.record(
        user_id=uid,
        tenant_id=tid,
        result="success",
        reason="login",
        ip_address="1.1.1.1",
        user_agent="agent",
    )

    assert repo.events  # event persisted
    assert activity.calls[0]["action"] == "auth.login.success"
    assert activity.calls[0]["metadata"] == {"user_id": str(uid), "tenant_id": str(tid)}


@pytest.mark.asyncio
async def test_password_policy_manager_rejects_recent_reuse() -> None:
    repo = _PasswordRepo()
    user_id = uuid4()
    repo.history = [
        PasswordHistoryEntry(
            user_id=user_id,
            password_hash=get_password_hash("RecentP@ssword123"),
            password_pepper_version="v2",
            created_at=datetime.now(UTC),
        )
    ]
    settings = Settings()
    settings.auth_password_history_count = 3
    manager = PasswordPolicyManager(cast(UserRepository, repo), settings)

    with pytest.raises(PasswordReuseError):
        await manager.enforce_history(user_id, "RecentP@ssword123")

    await manager.trim_history(user_id)
    assert repo.trim_calls == [3]


@pytest.mark.asyncio
async def test_lockout_manager_locks_after_threshold() -> None:
    settings = Settings()
    settings.auth_lockout_threshold = 2
    settings.auth_lockout_window_minutes = 1
    settings.auth_lockout_duration_minutes = 1
    repo = _LockoutRepo()
    events_repo = _LoginEventRepo()
    recorder = LoginEventRecorder(cast(UserRepository, events_repo))
    manager = LockoutManager(cast(UserRepository, repo), settings, recorder)
    user = _user_record()
    tenant = user.memberships[0].tenant_id

    await manager.handle_failed_login(user, tenant, "1.1.1.1", "ua")
    with pytest.raises(UserLockedError):
        await manager.handle_failed_login(user, tenant, "1.1.1.1", "ua")

    assert repo.status[user.id] == UserStatus.LOCKED
    assert repo.locked == {user.id}
    last_event = events_repo.events[-1]
    assert last_event.result == "locked"


def test_membership_resolution_multi_tenant_requires_context() -> None:
    memberships = [
        TenantMembershipDTO(tenant_id=uuid4(), role=TenantRole.ADMIN, created_at=datetime.now(UTC)),
        TenantMembershipDTO(tenant_id=uuid4(), role=TenantRole.MEMBER, created_at=datetime.now(UTC)),
    ]
    with pytest.raises(TenantContextRequiredError):
        resolve_membership(memberships, None)


def test_membership_resolution_unknown_tenant_raises() -> None:
    membership = TenantMembershipDTO(
        tenant_id=uuid4(), role=TenantRole.ADMIN, created_at=datetime.now(UTC)
    )
    with pytest.raises(MembershipNotFoundError):
        resolve_membership([membership], uuid4())


def test_scopes_for_role_variants() -> None:
    assert "billing:manage" in scopes_for_role(TenantRole.ADMIN)
    assert "conversations:write" in scopes_for_role(TenantRole.MEMBER)
    assert scopes_for_role(TenantRole.VIEWER) == ["conversations:read", "tools:read"]


@pytest.mark.asyncio
async def test_redis_login_throttle_blocks_after_threshold() -> None:
    client = FakeRedis()
    throttle = RedisLoginThrottle(client, threshold=2, window_seconds=60, block_seconds=60)
    ip = "10.0.0.5"
    await throttle.register_failure(ip)
    await throttle.register_failure(ip)

    with pytest.raises(IpThrottledError):
        await throttle.ensure_allowed(ip)


def test_build_user_service_missing_repo_raises(monkeypatch) -> None:
    from app.services.users import factory as user_factory

    monkeypatch.setattr(user_factory, "get_user_repository", lambda _: None)
    monkeypatch.setattr(user_factory, "build_ip_throttler", lambda _settings: NullLoginThrottle())
    monkeypatch.setattr(user_factory, "get_activity_service", lambda: _RecordingActivity())

    with pytest.raises(RuntimeError):
        build_user_service(settings=Settings())
