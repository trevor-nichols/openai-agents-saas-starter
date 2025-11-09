"""User domain service wrapping persistence, hashing, and lockout logic."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from app.core.config import Settings, get_settings
from app.core.security import PASSWORD_HASH_VERSION, get_password_hash, verify_password
from app.domain.users import (
    AuthenticatedUser,
    TenantMembershipDTO,
    UserCreate,
    UserCreatePayload,
    UserLoginEventDTO,
    UserRecord,
    UserRepository,
    UserStatus,
)
from app.infrastructure.persistence.auth.user_repository import get_user_repository
from app.observability.logging import log_event

logger = logging.getLogger("anything-agents.services.user")


class UserServiceError(RuntimeError):
    """Base class for user-service errors."""


class InvalidCredentialsError(UserServiceError):
    """Raised when supplied credentials fail validation."""


class UserLockedError(UserServiceError):
    """Raised when authentication is attempted against a locked user."""


class UserDisabledError(UserServiceError):
    """Raised when a disabled or pending user attempts to login."""


class TenantContextRequiredError(UserServiceError):
    """Raised when a multi-tenant user does not specify tenant context."""


class MembershipNotFoundError(UserServiceError):
    """Raised when a tenant is not associated with the user."""


class UserService:
    def __init__(
        self,
        repository: UserRepository,
        *,
        settings: Settings | None = None,
    ) -> None:
        if repository is None:
            raise RuntimeError("UserRepository is required for UserService.")
        self._repository = repository
        self._settings = settings or get_settings()

    async def register_user(self, payload: UserCreate) -> UserRecord:
        hashed = get_password_hash(payload.password)
        create_payload = UserCreatePayload(
            email=payload.email,
            password_hash=hashed,
            password_pepper_version=PASSWORD_HASH_VERSION,
            tenant_id=payload.tenant_id,
            role=payload.role,
            display_name=payload.display_name,
        )
        user = await self._repository.create_user(create_payload)
        logger.info("Registered user %s", user.email)
        return user

    async def authenticate(
        self,
        *,
        email: str,
        password: str,
        tenant_id: UUID | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> AuthenticatedUser:
        user = await self._repository.get_user_by_email(email)
        if user is None:
            logger.warning("Login attempt for unknown email: %s", email)
            raise InvalidCredentialsError("Invalid email or password.")

        membership = self._resolve_membership(user.memberships, tenant_id)
        await self._ensure_account_active(user, membership.tenant_id, ip_address, user_agent)

        verification = verify_password(password, user.password_hash)
        if not verification.is_valid:
            await self._handle_failed_login(user, membership.tenant_id, ip_address, user_agent)
            raise InvalidCredentialsError("Invalid email or password.")

        if verification.requires_rehash:
            await self._repository.update_password_hash(
                user.id,
                get_password_hash(password),
                password_pepper_version=PASSWORD_HASH_VERSION,
            )

        await self._repository.reset_lockout_counter(user.id)
        await self._repository.clear_user_lock(user.id)
        await self._record_login_event(
            user_id=user.id,
            tenant_id=membership.tenant_id,
            result="success",
            reason="login",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        log_event(
            "auth.login",
            result="success",
            user_id=str(user.id),
            tenant_id=str(membership.tenant_id),
        )
        return AuthenticatedUser(
            user_id=user.id,
            tenant_id=membership.tenant_id,
            email=user.email,
            role=membership.role,
            scopes=self._scopes_for_role(membership.role),
        )

    async def load_active_user(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthenticatedUser:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError("Unknown user.")
        membership = self._resolve_membership(user.memberships, tenant_id)
        await self._ensure_account_active(user, membership.tenant_id, ip_address, user_agent)
        return AuthenticatedUser(
            user_id=user.id,
            tenant_id=membership.tenant_id,
            email=user.email,
            role=membership.role,
            scopes=self._scopes_for_role(membership.role),
        )

    async def _handle_failed_login(
        self,
        user: UserRecord,
        tenant_id: UUID,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        window = int(self._settings.auth_lockout_window_minutes * 60)
        failures = await self._repository.increment_lockout_counter(user.id, ttl_seconds=window)
        await self._record_login_event(
            user_id=user.id,
            tenant_id=tenant_id,
            result="failure",
            reason="invalid_password",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        threshold = self._settings.auth_lockout_threshold
        if failures >= threshold:
            await self._repository.update_user_status(user.id, UserStatus.LOCKED)
            duration = int(self._settings.auth_lockout_duration_minutes * 60)
            await self._repository.mark_user_locked(user.id, duration_seconds=duration)
            await self._record_login_event(
                user_id=user.id,
                tenant_id=tenant_id,
                result="locked",
                reason="lockout_threshold",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            log_event(
                "auth.lockout", user_id=str(user.id), tenant_id=str(tenant_id), attempts=failures
            )
            raise UserLockedError("Account locked due to repeated failures.")

    async def _ensure_account_active(
        self,
        user: UserRecord,
        tenant_id: UUID,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        if user.status == UserStatus.DISABLED or user.status == UserStatus.PENDING:
            reason = "disabled" if user.status == UserStatus.DISABLED else "pending"
            await self._record_login_event(
                user_id=user.id,
                tenant_id=tenant_id,
                result="failure",
                reason=reason,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise UserDisabledError(f"User is {user.status.value}.")

        if user.status == UserStatus.LOCKED:
            if await self._repository.is_user_locked(user.id):
                await self._record_login_event(
                    user_id=user.id,
                    tenant_id=tenant_id,
                    result="locked",
                    reason="status_locked",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                raise UserLockedError("Account is locked.")
            await self._repository.update_user_status(user.id, UserStatus.ACTIVE)
            await self._repository.reset_lockout_counter(user.id)
            await self._repository.clear_user_lock(user.id)

    def _resolve_membership(
        self,
        memberships: Sequence[TenantMembershipDTO],
        tenant_id: UUID | None,
    ) -> TenantMembershipDTO:
        if not memberships:
            raise MembershipNotFoundError("User is not assigned to any tenant.")
        if tenant_id:
            for membership in memberships:
                if membership.tenant_id == tenant_id:
                    return membership
            raise MembershipNotFoundError("User is not a member of the requested tenant.")
        if len(memberships) > 1:
            raise TenantContextRequiredError("Tenant context required for multi-tenant users.")
        return memberships[0]

    async def _record_login_event(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        result: str,
        reason: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        event = UserLoginEventDTO(
            user_id=user_id,
            tenant_id=tenant_id,
            ip_hash=self._hash_ip(ip_address),
            user_agent=user_agent,
            result=result,  # type: ignore[arg-type]
            reason=reason,
            created_at=datetime.now(UTC),
        )
        await self._repository.record_login_event(event)

    def _hash_ip(self, ip_address: str | None) -> str:
        if not ip_address:
            return "unknown"
        digest = hashlib.sha256(ip_address.encode("utf-8"))
        return digest.hexdigest()

    def _scopes_for_role(self, role: str) -> list[str]:
        normalized = role.lower()
        if normalized in {"admin", "owner"}:
            return [
                "conversations:read",
                "conversations:write",
                "conversations:delete",
                "tools:read",
                "billing:read",
                "billing:manage",
                "support:read",
            ]
        if normalized in {"member", "editor"}:
            return [
                "conversations:read",
                "conversations:write",
                "tools:read",
            ]
        return [
            "conversations:read",
            "tools:read",
        ]


_DEFAULT_SERVICE: UserService | None = None


def get_user_service() -> UserService:
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        repository = get_user_repository()
        if repository is None:
            raise RuntimeError(
                "User repository is not configured. "
                "Run Postgres migrations and provide DATABASE_URL."
            )
        _DEFAULT_SERVICE = UserService(repository)
    return _DEFAULT_SERVICE
