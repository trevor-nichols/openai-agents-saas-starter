"""Service orchestration for tenant lifecycle transitions."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from app.core.settings import Settings, get_settings
from app.domain.tenant_accounts import TenantAccount, TenantAccountStatus
from app.observability.logging import log_event
from app.services.activity import activity_service
from app.services.billing import BillingError, BillingService, SubscriptionNotFoundError
from app.services.tenant.tenant_account_service import (
    TenantAccountService,
    get_tenant_account_service,
)

Clock = Callable[[], datetime]
SettingsFactory = Callable[[], Settings]


class TenantLifecycleError(Exception):
    """Base error for tenant lifecycle operations."""


class TenantLifecycleBillingError(TenantLifecycleError):
    """Raised when billing integration fails during lifecycle transitions."""


class TenantLifecycleService:
    """Coordinates tenant account lifecycle and downstream integrations."""

    def __init__(
        self,
        *,
        tenant_account_service: TenantAccountService | None = None,
        billing_service: BillingService | None = None,
        settings_factory: SettingsFactory | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._tenant_account_service = tenant_account_service
        self._billing_service = billing_service
        self._settings_factory = settings_factory or get_settings
        self._clock = clock or (lambda: datetime.now(UTC))

    def set_tenant_account_service(self, service: TenantAccountService) -> None:
        self._tenant_account_service = service

    def set_billing_service(self, service: BillingService | None) -> None:
        self._billing_service = service

    def _require_tenant_account_service(self) -> TenantAccountService:
        if self._tenant_account_service is None:
            self._tenant_account_service = get_tenant_account_service()
        return self._tenant_account_service

    async def suspend_tenant(
        self,
        tenant_id: UUID,
        *,
        actor_user_id: UUID | None,
        actor_role: str | None,
        reason: str | None,
    ) -> TenantAccount:
        account = await self._require_tenant_account_service().get_account(tenant_id)
        if account.status == TenantAccountStatus.SUSPENDED:
            return account
        updated = await self._require_tenant_account_service().suspend_account(
            tenant_id,
            actor_user_id=actor_user_id,
            reason=reason,
        )
        await self._record_lifecycle_event(
            tenant_id=tenant_id,
            event="suspended",
            from_status=account.status,
            to_status=updated.status,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            reason=reason,
        )
        return updated

    async def reactivate_tenant(
        self,
        tenant_id: UUID,
        *,
        actor_user_id: UUID | None,
        actor_role: str | None,
        reason: str | None,
    ) -> TenantAccount:
        account = await self._require_tenant_account_service().get_account(tenant_id)
        if account.status == TenantAccountStatus.ACTIVE:
            return account
        updated = await self._require_tenant_account_service().reactivate_account(
            tenant_id,
            actor_user_id=actor_user_id,
            reason=reason,
        )
        await self._record_lifecycle_event(
            tenant_id=tenant_id,
            event="reactivated",
            from_status=account.status,
            to_status=updated.status,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            reason=reason,
        )
        return updated

    async def deprovision_tenant(
        self,
        tenant_id: UUID,
        *,
        actor_user_id: UUID | None,
        actor_role: str | None,
        reason: str | None,
    ) -> TenantAccount:
        account = await self._require_tenant_account_service().get_account(tenant_id)
        if account.status == TenantAccountStatus.DEPROVISIONED:
            return account

        if account.status != TenantAccountStatus.DEPROVISIONING:
            previous_status = account.status
            account = await self._require_tenant_account_service().begin_deprovision(
                tenant_id,
                actor_user_id=actor_user_id,
                reason=reason,
            )
            await self._record_lifecycle_event(
                tenant_id=tenant_id,
                event="deprovisioning_started",
                from_status=previous_status,
                to_status=account.status,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                reason=reason,
            )

        await self._cancel_billing_if_enabled(tenant_id)

        finalized = await self._require_tenant_account_service().finalize_deprovision(
            tenant_id,
            actor_user_id=actor_user_id,
            reason=reason,
        )
        await self._record_lifecycle_event(
            tenant_id=tenant_id,
            event="deprovisioned",
            from_status=TenantAccountStatus.DEPROVISIONING,
            to_status=finalized.status,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            reason=reason,
        )
        return finalized

    async def _cancel_billing_if_enabled(self, tenant_id: UUID) -> None:
        settings = self._settings_factory()
        if not settings.enable_billing:
            return
        if self._billing_service is None:
            raise TenantLifecycleBillingError("Billing service is not configured.")
        try:
            await self._billing_service.cancel_subscription(
                str(tenant_id),
                cancel_at_period_end=False,
            )
        except SubscriptionNotFoundError:
            return
        except BillingError as exc:
            log_event(
                "tenant.lifecycle.billing_cancel_failed",
                level="warning",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            raise TenantLifecycleBillingError(str(exc)) from exc

    async def _record_lifecycle_event(
        self,
        *,
        tenant_id: UUID,
        event: str,
        from_status: TenantAccountStatus | None,
        to_status: TenantAccountStatus,
        actor_user_id: UUID | None,
        actor_role: str | None,
        reason: str | None,
    ) -> None:
        metadata: dict[str, object] = {
            "event": event,
            "to_status": to_status.value,
        }
        if from_status is not None:
            metadata["from_status"] = from_status.value
        if reason:
            metadata["reason"] = reason

        try:
            await activity_service.record(
                tenant_id=str(tenant_id),
                action="tenant.lifecycle",
                actor_id=str(actor_user_id) if actor_user_id else None,
                actor_type="user" if actor_user_id else "system",
                actor_role=actor_role,
                object_type="tenant",
                object_id=str(tenant_id),
                status="success",
                source="api",
                metadata=metadata,
                created_at=self._clock(),
            )
        except Exception:  # pragma: no cover - best effort
            log_event(
                "tenant.lifecycle.audit_failed",
                level="warning",
                tenant_id=str(tenant_id),
                lifecycle_event=event,
            )


def build_tenant_lifecycle_service(
    *,
    tenant_account_service: TenantAccountService | None = None,
    billing_service: BillingService | None = None,
    settings_factory: SettingsFactory | None = None,
) -> TenantLifecycleService:
    return TenantLifecycleService(
        tenant_account_service=tenant_account_service,
        billing_service=billing_service,
        settings_factory=settings_factory,
    )


def get_tenant_lifecycle_service() -> TenantLifecycleService:
    from app.bootstrap.container import get_container

    container = get_container()
    if container.tenant_lifecycle_service is None:
        container.tenant_lifecycle_service = build_tenant_lifecycle_service()
    return container.tenant_lifecycle_service


class _TenantLifecycleHandle:
    def __getattr__(self, name: str):
        if name == "get_tenant_lifecycle_service":
            return get_tenant_lifecycle_service
        return getattr(get_tenant_lifecycle_service(), name)


tenant_lifecycle_service = _TenantLifecycleHandle()


__all__ = [
    "TenantLifecycleBillingError",
    "TenantLifecycleError",
    "TenantLifecycleService",
    "build_tenant_lifecycle_service",
    "get_tenant_lifecycle_service",
    "tenant_lifecycle_service",
]
