"""Unit tests for PasswordRecoveryService."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from app.bootstrap import get_container
from app.domain.password_reset import PasswordResetTokenRecord
from app.domain.tenant_roles import TenantRole
from app.domain.users import TenantMembershipDTO, UserRecord, UserRepository, UserStatus
from app.services.signup.password_recovery_service import (
    InvalidPasswordResetTokenError,
    PasswordRecoveryService,
)
from app.services.users import (
    InvalidCredentialsError,
    PasswordPolicyViolationError,
    PasswordReuseError,
    UserService,
)


class FakeUserRepository:
    def __init__(self, user: UserRecord | None) -> None:
        self._user = user

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        if self._user and self._user.email == email:
            return self._user
        return None

    async def get_user_by_id(self, user_id: UUID) -> UserRecord | None:
        if self._user and self._user.id == user_id:
            return self._user
        return None


class FakeTokenStore:
    def __init__(self) -> None:
        self.records: dict[str, PasswordResetTokenRecord] = {}

    async def save(self, record: PasswordResetTokenRecord, *, ttl_seconds: int) -> None:
        self.records[record.token_id] = record

    async def get(self, token_id: str) -> PasswordResetTokenRecord | None:
        return self.records.get(token_id)

    async def delete(self, token_id: str) -> None:
        self.records.pop(token_id, None)


class FakeNotifier:
    def __init__(self) -> None:
        self.sent: deque[tuple[str, str, datetime]] = deque()

    async def send_password_reset(self, *, email: str, token: str, expires_at: datetime) -> None:
        self.sent.append((email, token, expires_at))


class FakeUserService:
    def __init__(self) -> None:
        self.reset_calls: list[tuple[UUID, str]] = []

    async def reset_password_via_token(self, *, user_id: UUID, new_password: str) -> None:
        self.reset_calls.append((user_id, new_password))


class RaisingUserService(FakeUserService):
    def __init__(self, exc: Exception) -> None:
        super().__init__()
        self._exc = exc

    async def reset_password_via_token(self, *, user_id: UUID, new_password: str) -> None:
        raise self._exc


class FakeAuthService:
    def __init__(self) -> None:
        self.revocations: list[tuple[UUID, str]] = []

    async def revoke_user_sessions(self, user_id: UUID, *, reason: str) -> None:
        self.revocations.append((user_id, reason))


@pytest.fixture
def sample_user() -> UserRecord:
    return UserRecord(
        id=uuid4(),
        email="owner@example.com",
        status=UserStatus.ACTIVE,
        password_hash="hash",
        password_pepper_version="v2",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        display_name=None,
        given_name=None,
        family_name=None,
        avatar_url=None,
        timezone=None,
        locale=None,
        memberships=[
            TenantMembershipDTO(
                tenant_id=uuid4(), role=TenantRole.ADMIN, created_at=datetime.now(UTC)
            )
        ],
        email_verified_at=datetime.now(UTC),
        platform_role=None,
    )


@pytest.fixture
def fake_auth() -> FakeAuthService:
    fake = FakeAuthService()
    cast(Any, get_container()).auth_service = fake
    return fake


@pytest.mark.asyncio
async def test_request_password_reset_stores_token(sample_user: UserRecord, fake_auth) -> None:
    repo = FakeUserRepository(sample_user)
    store = FakeTokenStore()
    notifier = FakeNotifier()
    user_service = FakeUserService()
    service = PasswordRecoveryService(
        cast(UserRepository, repo),
        store,
        notifier,
        user_service=cast(UserService, user_service),
    )

    await service.request_password_reset(
        email=sample_user.email,
        ip_address="203.0.113.1",
        user_agent="pytest",
    )

    assert len(store.records) == 1
    assert len(notifier.sent) == 1
    email, token, _ = notifier.sent[0]
    assert email == sample_user.email
    assert token.count(".") == 1


@pytest.mark.asyncio
async def test_confirm_password_reset_success(
    sample_user: UserRecord, fake_auth: FakeAuthService
) -> None:
    repo = FakeUserRepository(sample_user)
    store = FakeTokenStore()
    notifier = FakeNotifier()
    user_service = FakeUserService()
    service = PasswordRecoveryService(
        cast(UserRepository, repo),
        store,
        notifier,
        user_service=cast(UserService, user_service),
    )

    await service.request_password_reset(email=sample_user.email, ip_address=None, user_agent=None)
    _, token, _ = notifier.sent[0]

    await service.confirm_password_reset(
        token=token,
        new_password="ResetToken!!123",
        ip_address="198.51.100.10",
        user_agent="pytest",
    )

    assert user_service.reset_calls
    assert fake_auth.revocations
    assert not store.records


@pytest.mark.asyncio
async def test_confirm_password_reset_invalid_token(sample_user: UserRecord, fake_auth) -> None:
    repo = FakeUserRepository(sample_user)
    store = FakeTokenStore()
    notifier = FakeNotifier()
    user_service = FakeUserService()
    service = PasswordRecoveryService(
        cast(UserRepository, repo),
        store,
        notifier,
        user_service=cast(UserService, user_service),
    )

    with pytest.raises(InvalidPasswordResetTokenError):
        await service.confirm_password_reset(
            token="missing.token",
            new_password="Whatever!!123",
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_confirm_password_reset_policy_error_keeps_token(
    sample_user: UserRecord, fake_auth: FakeAuthService
) -> None:
    repo = FakeUserRepository(sample_user)
    store = FakeTokenStore()
    notifier = FakeNotifier()
    user_service = RaisingUserService(PasswordPolicyViolationError("too weak"))
    service = PasswordRecoveryService(
        cast(UserRepository, repo),
        store,
        notifier,
        user_service=cast(UserService, user_service),
    )

    await service.request_password_reset(email=sample_user.email, ip_address=None, user_agent=None)
    _, token, _ = notifier.sent[0]
    token_id = next(iter(store.records))

    with pytest.raises(PasswordPolicyViolationError):
        await service.confirm_password_reset(
            token=token,
            new_password="short",
            ip_address=None,
            user_agent=None,
        )

    assert token_id in store.records


@pytest.mark.asyncio
async def test_confirm_password_reset_reuse_error_keeps_token(
    sample_user: UserRecord, fake_auth: FakeAuthService
) -> None:
    repo = FakeUserRepository(sample_user)
    store = FakeTokenStore()
    notifier = FakeNotifier()
    user_service = RaisingUserService(PasswordReuseError("reuse"))
    service = PasswordRecoveryService(
        cast(UserRepository, repo),
        store,
        notifier,
        user_service=cast(UserService, user_service),
    )

    await service.request_password_reset(email=sample_user.email, ip_address=None, user_agent=None)
    _, token, _ = notifier.sent[0]
    token_id = next(iter(store.records))

    with pytest.raises(PasswordReuseError):
        await service.confirm_password_reset(
            token=token,
            new_password="SamePassword!!123",
            ip_address=None,
            user_agent=None,
        )

    assert token_id in store.records


@pytest.mark.asyncio
async def test_confirm_password_reset_invalid_credentials_consumes_token(
    sample_user: UserRecord, fake_auth: FakeAuthService
) -> None:
    repo = FakeUserRepository(sample_user)
    store = FakeTokenStore()
    notifier = FakeNotifier()
    user_service = RaisingUserService(InvalidCredentialsError("missing user"))
    service = PasswordRecoveryService(
        cast(UserRepository, repo),
        store,
        notifier,
        user_service=cast(UserService, user_service),
    )

    await service.request_password_reset(email=sample_user.email, ip_address=None, user_agent=None)
    _, token, _ = notifier.sent[0]

    with pytest.raises(InvalidPasswordResetTokenError):
        await service.confirm_password_reset(
            token=token,
            new_password="ValidPassword!!123",
            ip_address=None,
            user_agent=None,
        )

    assert not store.records
