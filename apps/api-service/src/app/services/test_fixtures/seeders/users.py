"""User seeding helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import PASSWORD_HASH_VERSION, get_password_hash
from app.infrastructure.persistence.auth.models.membership import TenantUserMembership
from app.infrastructure.persistence.auth.models.user import (
    PasswordHistory,
    UserAccount,
    UserProfile,
    UserStatus,
)
from app.infrastructure.persistence.tenants.models import TenantAccount
from app.services.test_fixtures.schemas import FixtureUser, FixtureUserResult


async def ensure_users(
    session: AsyncSession,
    tenant: TenantAccount,
    users: list[FixtureUser],
) -> dict[str, FixtureUserResult]:
    results: dict[str, FixtureUserResult] = {}
    for user_spec in users:
        results[user_spec.email] = await ensure_user(
            session=session,
            tenant=tenant,
            user_spec=user_spec,
        )
    return results


async def ensure_user(
    session: AsyncSession,
    tenant: TenantAccount,
    user_spec: FixtureUser,
) -> FixtureUserResult:
    normalized_email = user_spec.email.lower()
    hashed_password = get_password_hash(user_spec.password)
    now = datetime.now(UTC)

    user = await session.scalar(select(UserAccount).where(UserAccount.email == normalized_email))

    if user is None:
        user = UserAccount(
            id=uuid4(),
            email=normalized_email,
            password_hash=hashed_password,
            password_pepper_version=PASSWORD_HASH_VERSION,
            status=UserStatus.ACTIVE,
            email_verified_at=now if user_spec.verify_email else None,
            platform_role=user_spec.platform_role,
        )
        session.add(user)
    else:
        user.password_hash = hashed_password
        user.password_pepper_version = PASSWORD_HASH_VERSION
        user.status = UserStatus.ACTIVE
        user.platform_role = user_spec.platform_role
        if user_spec.verify_email:
            user.email_verified_at = now
        else:
            user.email_verified_at = None

    profile = await session.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if user_spec.display_name:
        if profile:
            profile.display_name = user_spec.display_name
        else:
            session.add(
                UserProfile(
                    id=uuid4(),
                    user_id=user.id,
                    display_name=user_spec.display_name,
                )
            )

    membership = await session.scalar(
        select(TenantUserMembership).where(
            TenantUserMembership.user_id == user.id,
            TenantUserMembership.tenant_id == tenant.id,
        )
    )
    if membership:
        membership.role = user_spec.role
    else:
        membership = TenantUserMembership(
            id=uuid4(),
            user_id=user.id,
            tenant_id=tenant.id,
            role=user_spec.role,
        )
        session.add(membership)

    existing_history = await session.scalar(
        select(PasswordHistory).where(
            PasswordHistory.user_id == user.id,
            PasswordHistory.password_hash == hashed_password,
        )
    )
    if existing_history is None:
        session.add(
            PasswordHistory(
                id=uuid4(),
                user_id=user.id,
                password_hash=hashed_password,
                password_pepper_version=PASSWORD_HASH_VERSION,
                created_at=now,
            )
        )

    return FixtureUserResult(user_id=str(user.id), role=membership.role)


__all__ = ["ensure_user", "ensure_users"]
