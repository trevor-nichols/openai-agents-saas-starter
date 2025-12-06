"""Login event recording utilities."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Literal, Protocol
from uuid import UUID

from app.domain.users import UserLoginEventDTO, UserRepository

logger = logging.getLogger("api-service.services.user.login-events")


class ActivityRecorder(Protocol):
    async def record(
        self,
        *,
        tenant_id: str,
        action: str,
        actor_id: str | None = None,
        actor_type: Any | None = None,
        status: Any = "success",
        source: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> object | None: ...


class LoginEventRecorder:
    def __init__(
        self,
        repository: UserRepository,
        *,
        activity_recorder: ActivityRecorder | None = None,
    ) -> None:
        self._repository = repository
        self._activity_recorder = activity_recorder

    async def record(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        result: Literal["success", "failure", "locked"],
        reason: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        event = UserLoginEventDTO(
            user_id=user_id,
            tenant_id=tenant_id,
            ip_hash=self._hash_ip(ip_address),
            user_agent=user_agent,
            result=result,
            reason=reason,
            created_at=datetime.now(UTC),
        )
        await self._repository.record_login_event(event)
        if not self._activity_recorder:
            return
        try:
            action = "auth.login.success" if result == "success" else "auth.login.failure"
            metadata = (
                {"user_id": str(user_id), "tenant_id": str(tenant_id)}
                if result == "success"
                else {"reason": reason or "unknown"}
            )
            await self._activity_recorder.record(
                tenant_id=str(tenant_id),
                action=action,
                actor_id=str(user_id),
                actor_type="user",
                status=result if result in {"success", "failure"} else "failure",
                source="api",
                user_agent=user_agent,
                ip_address=ip_address,
                metadata=metadata,
            )
        except Exception:  # pragma: no cover - best effort
            logger.debug("activity.log.login.skipped", exc_info=True)

    def _hash_ip(self, ip_address: str | None) -> str:
        if not ip_address:
            return "unknown"
        digest = hashlib.sha256(ip_address.encode("utf-8"))
        return digest.hexdigest()


__all__ = ["LoginEventRecorder", "ActivityRecorder"]
