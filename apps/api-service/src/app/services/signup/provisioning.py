"""Tenant + owner provisioning helpers for signup flows."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import PASSWORD_HASH_VERSION, get_password_hash
from app.domain.tenant_accounts import TenantAccountStatus
from app.domain.tenant_roles import TenantRole
from app.domain.users import UserStatus
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.auth.models.membership import TenantUserMembership
from app.infrastructure.persistence.auth.models.user import (
    PasswordHistory,
    UserAccount,
    UserProfile,
)
from app.infrastructure.persistence.auth.models.user import (
    UserStatus as DBUserStatus,
)
from app.infrastructure.persistence.tenants.account_repository import (
    PostgresTenantAccountRepository,
)
from app.services.signup.errors import EmailAlreadyRegisteredError, TenantSlugCollisionError
from app.services.tenant.tenant_account_service import (
    TenantAccountService,
    TenantAccountSlugCollisionError,
    get_tenant_account_service,
)


@dataclass(slots=True)
class SignupProvisioningOutcome:
    tenant_id: uuid.UUID
    tenant_slug: str
    user_id: uuid.UUID


class SignupProvisioningService:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        tenant_account_service: TenantAccountService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._tenant_account_service = tenant_account_service

    def _get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._session_factory = get_async_sessionmaker()
        return self._session_factory

    def _get_tenant_account_service(self) -> TenantAccountService:
        if self._tenant_account_service is None:
            self._tenant_account_service = get_tenant_account_service()
        return self._tenant_account_service

    async def provision_tenant_owner(
        self,
        *,
        tenant_name: str,
        email: str,
        password: str,
        display_name: str | None,
    ) -> SignupProvisioningOutcome:
        session_factory = self._get_session_factory()
        async with session_factory() as session:
            async with session.begin():
                tenant_service = self._get_tenant_account_service().with_repository(
                    PostgresTenantAccountRepository.for_session(session)
                )
                try:
                    tenant_account = await tenant_service.create_account(
                        name=tenant_name,
                        status=TenantAccountStatus.PROVISIONING,
                        reason="signup",
                        allow_slug_suffix=True,
                    )
                except TenantAccountSlugCollisionError as exc:
                    raise TenantSlugCollisionError(str(exc)) from exc

                user_id = await self._create_owner_records(
                    session,
                    tenant_id=tenant_account.id,
                    email=email,
                    password=password,
                    display_name=display_name,
                    status=UserStatus.PENDING,
                )

        return SignupProvisioningOutcome(
            tenant_id=tenant_account.id,
            tenant_slug=tenant_account.slug,
            user_id=user_id,
        )

    async def _create_owner_records(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        email: str,
        password: str,
        display_name: str | None,
        status: UserStatus,
    ) -> uuid.UUID:
        normalized_email = email.strip().lower()
        hashed_password = get_password_hash(password)

        existing_user = await session.scalar(
            select(UserAccount.id).where(UserAccount.email == normalized_email)
        )
        if existing_user:
            raise EmailAlreadyRegisteredError("Email already registered.")

        user_id = uuid.uuid4()
        session.add(
            UserAccount(
                id=user_id,
                email=normalized_email,
                password_hash=hashed_password,
                password_pepper_version=PASSWORD_HASH_VERSION,
                status=DBUserStatus(status.value),
            )
        )

        if display_name:
            session.add(
                UserProfile(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    display_name=display_name,
                )
            )

        session.add(
            TenantUserMembership(
                id=uuid.uuid4(),
                user_id=user_id,
                tenant_id=tenant_id,
                role=TenantRole.OWNER,
            )
        )

        session.add(
            PasswordHistory(
                id=uuid.uuid4(),
                user_id=user_id,
                password_hash=hashed_password,
                password_pepper_version=PASSWORD_HASH_VERSION,
                created_at=datetime.now(UTC),
            )
        )

        try:
            await session.flush()
        except IntegrityError as exc:  # pragma: no cover - rare email race
            raise EmailAlreadyRegisteredError("Email already registered.") from exc

        return user_id

    async def finalize_provisioning(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: str,
    ) -> None:
        session_factory = self._get_session_factory()
        async with session_factory() as session:
            async with session.begin():
                tenant_service = self._get_tenant_account_service().with_repository(
                    PostgresTenantAccountRepository.for_session(session)
                )
                await tenant_service.complete_provisioning(
                    tenant_id,
                    actor_user_id=user_id,
                    reason=reason,
                )
                await session.execute(
                    update(UserAccount)
                    .where(UserAccount.id == user_id)
                    .values(status=DBUserStatus.ACTIVE, updated_at=datetime.now(UTC))
                )

    async def fail_provisioning(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: str,
    ) -> None:
        session_factory = self._get_session_factory()
        async with session_factory() as session:
            async with session.begin():
                tenant_service = self._get_tenant_account_service().with_repository(
                    PostgresTenantAccountRepository.for_session(session)
                )
                await tenant_service.deprovision_account(
                    tenant_id,
                    actor_user_id=None,
                    reason=reason,
                )
                await session.execute(
                    update(UserAccount)
                    .where(UserAccount.id == user_id)
                    .values(status=DBUserStatus.DISABLED, updated_at=datetime.now(UTC))
                )


__all__ = ["SignupProvisioningOutcome", "SignupProvisioningService"]
