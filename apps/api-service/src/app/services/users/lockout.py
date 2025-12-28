"""Account lockout and status helpers."""

from __future__ import annotations

import logging
from math import ceil
from uuid import UUID

from app.core.settings import Settings
from app.domain.users import UserRecord, UserRepository, UserStatus
from app.observability.logging import log_event

from .errors import UserDisabledError, UserLockedError
from .login_events import LoginEventRecorder

logger = logging.getLogger("api-service.services.user.lockout")


class LockoutManager:
    def __init__(
        self,
        repository: UserRepository,
        settings: Settings,
        login_events: LoginEventRecorder,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._login_events = login_events

    async def handle_failed_login(
        self,
        user: UserRecord,
        tenant_id: UUID,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        window = max(1, ceil(self._settings.auth_lockout_window_minutes * 60))
        failures = await self._repository.increment_lockout_counter(user.id, ttl_seconds=window)
        await self._login_events.record(
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
            duration = max(1, ceil(self._settings.auth_lockout_duration_minutes * 60))
            await self._repository.mark_user_locked(user.id, duration_seconds=duration)
            await self._login_events.record(
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

    async def ensure_account_active(
        self,
        user: UserRecord,
        tenant_id: UUID,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        if user.status == UserStatus.DISABLED or user.status == UserStatus.PENDING:
            reason = "disabled" if user.status == UserStatus.DISABLED else "pending"
            await self._login_events.record(
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
                await self._login_events.record(
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


__all__ = ["LockoutManager"]
