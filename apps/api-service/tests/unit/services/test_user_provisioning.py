"""Unit tests for user provisioning idempotency."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from app.domain.tenant_roles import TenantRole
from app.domain.users import UserProfilePatch, UserRecord, UserStatus
from app.services.users.provisioning import (
    UserProvisioningRequest,
    UserProvisioningService,
)


class FakeUserRepo:
    def __init__(self, user: UserRecord) -> None:
        self.user = user
        self.verified: list[UUID] = []
        self.profile_updates: list[tuple[UUID, UserProfilePatch, set[str]]] = []

    async def create_user(self, *_args, **_kwargs):  # pragma: no cover - not used
        raise AssertionError("create_user should not be called in this test")

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        return self.user if self.user.email == email else None

    async def upsert_user_profile(
        self,
        user_id: UUID,
        update: UserProfilePatch,
        *,
        provided_fields: set[str],
    ) -> None:
        self.profile_updates.append((user_id, update, provided_fields))

    async def mark_email_verified(self, user_id: UUID, *, timestamp: datetime) -> None:
        self.verified.append(user_id)


class FakeMembershipRepo:
    def __init__(self, exists: bool) -> None:
        self.exists = exists
        self.add_calls = 0

    async def membership_exists(self, *, tenant_id: UUID, user_id: UUID) -> bool:
        return self.exists

    async def add_member(self, *, tenant_id: UUID, user_id: UUID, role: TenantRole):
        self.add_calls += 1
        raise AssertionError("add_member should not be called when membership exists")


@pytest.mark.asyncio
async def test_provision_user_idempotent_when_membership_exists() -> None:
    user = _build_user("owner@example.com")
    user_repo = FakeUserRepo(user)
    membership_repo = FakeMembershipRepo(exists=True)
    service = UserProvisioningService(
        user_repository=cast(Any, user_repo),
        membership_repository=cast(Any, membership_repo),
    )

    result = await service.provision_user(
        request=UserProvisioningRequest(
            tenant_id=uuid4(),
            email=user.email,
            default_role=TenantRole.MEMBER,
            display_name=None,
            email_verified=True,
            existing_user=user,
        )
    )

    assert result.user.id == user.id
    assert result.membership_added is False
    assert membership_repo.add_calls == 0
    assert user.id in user_repo.verified


def _build_user(email: str) -> UserRecord:
    now = datetime.now(UTC)
    return UserRecord(
        id=uuid4(),
        email=email,
        status=UserStatus.ACTIVE,
        password_hash="hash",
        password_pepper_version="v2",
        created_at=now,
        updated_at=now,
        display_name=None,
        given_name=None,
        family_name=None,
        avatar_url=None,
        timezone=None,
        locale=None,
        memberships=[],
        email_verified_at=None,
        platform_role=None,
    )
