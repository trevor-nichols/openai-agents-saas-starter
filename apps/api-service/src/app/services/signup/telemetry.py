"""Telemetry helpers for signup flows."""

from __future__ import annotations

import logging

from app.observability.logging import log_event
from app.services.activity import activity_service

logger = logging.getLogger(__name__)


class SignupTelemetry:
    async def record_signup_success(
        self,
        *,
        tenant_id: str,
        tenant_slug: str,
        user_id: str,
        plan_code: str | None,
        invite_id: str | None,
        user_agent: str | None,
        ip_address: str | None,
    ) -> None:
        log_event(
            "signup.completed",
            result="success",
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            plan_code=plan_code or "none",
            invite_id=invite_id,
        )

        try:
            await activity_service.record(
                tenant_id=str(tenant_id),
                action="auth.signup.success",
                actor_id=str(user_id),
                actor_type="user",
                object_type="tenant",
                object_id=str(tenant_id),
                source="api",
                user_agent=user_agent,
                ip_address=ip_address,
                metadata={"user_id": str(user_id), "tenant_id": str(tenant_id)},
            )
        except Exception:  # pragma: no cover - best effort
            logger.debug("activity.log.signup.skipped", exc_info=True)


__all__ = ["SignupTelemetry"]
