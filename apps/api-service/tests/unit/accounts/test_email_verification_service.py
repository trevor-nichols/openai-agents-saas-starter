"""Unit tests for EmailVerificationService."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.bootstrap import get_container
from app.domain.email_verification import (
    EmailVerificationTokenRecord,
    EmailVerificationTokenStore,
)
from app.domain.tenant_roles import TenantRole
from app.domain.users import TenantMembershipDTO, UserRecord, UserRepository, UserStatus
from app.services.signup.email_verification_service import (
    EmailVerificationError,
    EmailVerificationService,
    InvalidEmailVerificationTokenError,
)


class FakeUserRepository:
    def __init__(self, user: UserRecord | None) -> None:
        self._user = user
        self.marked: list[UUID] = []

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        if self._user and self._user.email.lower() == email.strip().lower():
            return self._user
        return None

    async def get_user_by_id(self, user_id: UUID) -> UserRecord | None:
        if self._user and self._user.id == user_id:
            return self._user
        return None

    async def mark_email_verified(self, user_id: UUID, *, timestamp: datetime) -> None:
        self.marked.append(user_id)
        if self._user and self._user.id == user_id:
            self._user.email_verified_at = timestamp


class FakeTokenStore:
    def __init__(self) -> None:
        self.saved: dict[str, EmailVerificationTokenRecord] = {}

    async def save(
        self,
        record: EmailVerificationTokenRecord,
        *,
        ttl_seconds: int,
    ) -> None:
        self.saved[record.token_id] = record

    async def get(self, token_id: str) -> EmailVerificationTokenRecord | None:
        return self.saved.get(token_id)

    async def delete(self, token_id: str) -> None:
        self.saved.pop(token_id, None)


class FakeNotifier:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_verification(self, *, email: str, token: str, expires_at: datetime) -> None:
        self.sent.append((email, token))


@pytest.fixture
def sample_user() -> UserRecord:
    return UserRecord(
        id=uuid4(),
        email="owner@example.com",
        status=UserStatus.PENDING,
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
                tenant_id=uuid4(), role=TenantRole.OWNER, created_at=datetime.now(UTC)
            )
        ],
        email_verified_at=None,
        platform_role=None,
    )


@pytest.mark.asyncio
async def test_send_verification_email_saves_token(sample_user: UserRecord) -> None:
    repo = FakeUserRepository(sample_user)
    store = FakeTokenStore()
    notifier = FakeNotifier()

    fake_auth = AsyncMock()
    fake_auth.revoke_user_sessions = AsyncMock(return_value=None)
    cast(Any, get_container()).auth_service = fake_auth

    service = EmailVerificationService(
        cast(UserRepository, repo),
        cast(EmailVerificationTokenStore, store),
        notifier,
    )

    sent = await service.send_verification_email(
        user_id=str(sample_user.id),
        email=None,
        ip_address="198.51.100.5",
        user_agent="pytest",
    )

    assert sent is True
    assert store.saved
    assert notifier.sent


@pytest.mark.asyncio
async def test_send_verification_skips_when_verified(sample_user: UserRecord) -> None:
    sample_user.email_verified_at = datetime.now(UTC) - timedelta(days=1)
    repo = FakeUserRepository(sample_user)
    service = EmailVerificationService(
        cast(UserRepository, repo),
        cast(EmailVerificationTokenStore, FakeTokenStore()),
        FakeNotifier(),
    )

    sent = await service.send_verification_email(
        user_id=str(sample_user.id),
        email=None,
        ip_address=None,
        user_agent=None,
    )

    assert sent is False


@pytest.mark.asyncio
async def test_verify_token_updates_user(sample_user: UserRecord) -> None:
    repo = FakeUserRepository(sample_user)
    store = FakeTokenStore()
    notifier = FakeNotifier()

    fake_auth = AsyncMock()
    fake_auth.revoke_user_sessions = AsyncMock(return_value=None)
    cast(Any, get_container()).auth_service = fake_auth

    service = EmailVerificationService(
        cast(UserRepository, repo),
        cast(EmailVerificationTokenStore, store),
        notifier,
    )

    sent = await service.send_verification_email(
        user_id=str(sample_user.id),
        email=None,
        ip_address=None,
        user_agent=None,
    )
    assert sent is True
    token = next(iter(notifier.sent))[1]

    await service.verify_token(token=token, ip_address=None, user_agent=None)

    assert repo.marked == [sample_user.id]


@pytest.mark.asyncio
async def test_verify_token_rejects_invalid(sample_user: UserRecord) -> None:
    repo = FakeUserRepository(sample_user)
    service = EmailVerificationService(
        cast(UserRepository, repo),
        cast(EmailVerificationTokenStore, FakeTokenStore()),
        FakeNotifier(),
    )

    with pytest.raises(InvalidEmailVerificationTokenError):
        await service.verify_token(token="missing.token", ip_address=None, user_agent=None)


@pytest.mark.asyncio
async def test_issue_token_for_testing_returns_token(sample_user: UserRecord) -> None:
    repo = FakeUserRepository(sample_user)
    store = FakeTokenStore()
    service = EmailVerificationService(
        cast(UserRepository, repo),
        cast(EmailVerificationTokenStore, store),
        FakeNotifier(),
    )

    result = await service.issue_token_for_testing(
        email=sample_user.email,
        ip_address="198.51.100.5",
        user_agent="pytest",
    )

    assert result.token.count(".") == 1
    assert result.user_id == sample_user.id
    token_id = result.token.split(".", 1)[0]
    assert token_id in store.saved


@pytest.mark.asyncio
async def test_issue_token_for_testing_rejects_verified_user(sample_user: UserRecord) -> None:
    sample_user.email_verified_at = datetime.now(UTC)
    repo = FakeUserRepository(sample_user)
    service = EmailVerificationService(
        cast(UserRepository, repo),
        cast(EmailVerificationTokenStore, FakeTokenStore()),
        FakeNotifier(),
    )

    with pytest.raises(EmailVerificationError):
        await service.issue_token_for_testing(
            email=sample_user.email,
            ip_address=None,
            user_agent=None,
        )
