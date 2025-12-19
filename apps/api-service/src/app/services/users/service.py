"""User domain service orchestrating auth, password, and login policy."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from uuid import UUID

from app.core.security import PASSWORD_HASH_VERSION, get_password_hash, verify_password
from app.core.settings import Settings
from app.domain.users import (
    AuthenticatedUser,
    TenantMembershipDTO,
    UserCreate,
    UserCreatePayload,
    UserProfileSummary,
    UserRecord,
    UserRepository,
)
from app.observability.logging import log_event

from .errors import InvalidCredentialsError
from .lockout import LockoutManager
from .login_events import ActivityRecorder, LoginEventRecorder
from .membership import resolve_membership
from .passwords import PasswordPolicyManager
from .scopes import scopes_for_role
from .throttling import LoginThrottle, NullLoginThrottle

logger = logging.getLogger("api-service.services.user")


class UserService:
    def __init__(
        self,
        repository: UserRepository,
        *,
        settings: Settings,
        ip_throttler: LoginThrottle | None = None,
        activity_recorder: ActivityRecorder | None = None,
        login_events: LoginEventRecorder | None = None,
        lockout_manager: LockoutManager | None = None,
        password_manager: PasswordPolicyManager | None = None,
        membership_resolver: Callable[
            [Sequence[TenantMembershipDTO], UUID | None], TenantMembershipDTO
        ]
        | None = None,
        scope_resolver: Callable[[str], list[str]] | None = None,
    ) -> None:
        if repository is None:
            raise RuntimeError("UserRepository is required for UserService.")
        self._repository = repository
        self._settings = settings
        self._ip_throttler = ip_throttler or NullLoginThrottle()
        self._membership_resolver = membership_resolver or resolve_membership
        self._scope_resolver = scope_resolver or scopes_for_role
        self._login_events = login_events or LoginEventRecorder(
            repository, activity_recorder=activity_recorder
        )
        self._lockout = lockout_manager or LockoutManager(
            repository, settings, self._login_events
        )
        self._passwords = password_manager or PasswordPolicyManager(repository, settings)
        self._activity_recorder = activity_recorder

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

    async def change_password(
        self,
        *,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError("Unknown user.")

        verification = verify_password(current_password, user.password_hash)
        if not verification.is_valid:
            raise InvalidCredentialsError("Invalid current password.")

        await self._passwords.enforce_history(user.id, new_password)
        self._passwords.validate_strength(new_password, hints=[user.email])
        hashed = get_password_hash(new_password)
        await self._repository.update_password_hash(
            user.id,
            hashed,
            password_pepper_version=PASSWORD_HASH_VERSION,
        )
        await self._passwords.trim_history(user.id)
        await self._repository.reset_lockout_counter(user.id)
        await self._repository.clear_user_lock(user.id)
        log_event("auth.password_change", result="success", user_id=str(user.id))
        await self._record_password_activity(user, tenant_id=None)

    async def admin_reset_password(
        self,
        *,
        target_user_id: UUID,
        tenant_id: UUID,
        new_password: str,
    ) -> None:
        user = await self._repository.get_user_by_id(target_user_id)
        if user is None:
            raise InvalidCredentialsError("Unknown user.")

        membership = self._membership_resolver(user.memberships, tenant_id)
        await self._passwords.enforce_history(user.id, new_password)
        self._passwords.validate_strength(new_password, hints=[user.email])
        hashed = get_password_hash(new_password)
        await self._repository.update_password_hash(
            user.id,
            hashed,
            password_pepper_version=PASSWORD_HASH_VERSION,
        )
        await self._passwords.trim_history(user.id)
        await self._repository.reset_lockout_counter(user.id)
        await self._repository.clear_user_lock(user.id)
        log_event(
            "auth.password_reset",
            result="success",
            user_id=str(user.id),
            tenant_id=str(membership.tenant_id),
        )
        await self._record_password_activity(user, tenant_id=membership.tenant_id)

    async def reset_password_via_token(self, *, user_id: UUID, new_password: str) -> None:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError("Unknown user.")
        await self._passwords.enforce_history(user.id, new_password)
        self._passwords.validate_strength(new_password, hints=[user.email])
        hashed = get_password_hash(new_password)
        await self._repository.update_password_hash(
            user.id,
            hashed,
            password_pepper_version=PASSWORD_HASH_VERSION,
        )
        await self._passwords.trim_history(user.id)
        await self._repository.reset_lockout_counter(user.id)
        await self._repository.clear_user_lock(user.id)
        log_event("auth.password_reset_token", result="success", user_id=str(user.id))
        tenant_id = user.memberships[0].tenant_id if user.memberships else None
        await self._record_password_activity(user, tenant_id=tenant_id)

    async def authenticate(
        self,
        *,
        email: str,
        password: str,
        tenant_id: UUID | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> AuthenticatedUser:
        await self._ip_throttler.ensure_allowed(ip_address)
        user = await self._repository.get_user_by_email(email)
        if user is None:
            logger.warning("Login attempt for unknown email: %s", email)
            await self._ip_throttler.register_failure(ip_address)
            raise InvalidCredentialsError("Invalid email or password.")

        membership = self._membership_resolver(user.memberships, tenant_id)
        await self._lockout.ensure_account_active(
            user, membership.tenant_id, ip_address, user_agent
        )

        verification = verify_password(password, user.password_hash)
        if not verification.is_valid:
            await self._ip_throttler.register_failure(ip_address)
            await self._lockout.handle_failed_login(
                user, membership.tenant_id, ip_address, user_agent
            )
            raise InvalidCredentialsError("Invalid email or password.")

        if verification.requires_rehash:
            await self._repository.update_password_hash(
                user.id,
                get_password_hash(password),
                password_pepper_version=PASSWORD_HASH_VERSION,
            )

        await self._repository.reset_lockout_counter(user.id)
        await self._repository.clear_user_lock(user.id)
        await self._login_events.record(
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
            scopes=self._scope_resolver(membership.role),
            email_verified=user.email_verified_at is not None,
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
        membership = self._membership_resolver(user.memberships, tenant_id)
        await self._lockout.ensure_account_active(
            user, membership.tenant_id, ip_address, user_agent
        )
        return AuthenticatedUser(
            user_id=user.id,
            tenant_id=membership.tenant_id,
            email=user.email,
            role=membership.role,
            scopes=self._scope_resolver(membership.role),
            email_verified=user.email_verified_at is not None,
        )

    async def get_user_profile_summary(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
    ) -> UserProfileSummary:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError("Unknown user.")
        membership = self._membership_resolver(user.memberships, tenant_id)
        display_name = (
            user.display_name
            or " ".join(part for part in [user.given_name, user.family_name] if part)
            or None
        )
        return UserProfileSummary(
            user_id=user.id,
            tenant_id=membership.tenant_id,
            email=user.email,
            display_name=display_name,
            given_name=user.given_name,
            family_name=user.family_name,
            avatar_url=user.avatar_url,
            role=membership.role,
            email_verified=user.email_verified_at is not None,
        )

    async def _record_password_activity(
        self, user: UserRecord, tenant_id: UUID | None
    ) -> None:
        if not self._activity_recorder or not tenant_id:
            return
        try:
            await self._activity_recorder.record(
                tenant_id=str(tenant_id),
                action="auth.password.changed",
                actor_id=str(user.id),
                actor_type="user",
                status="success",
                metadata={"user_id": str(user.id)},
            )
        except Exception:  # pragma: no cover - best effort
            logger.debug("activity.log.password_change.skipped", exc_info=True)


__all__ = ["UserService"]
