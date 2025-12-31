"""Unit tests for tenant lifecycle service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.core.settings import Settings
from app.domain.tenant_accounts import TenantAccount, TenantAccountStatus
from app.services.billing.errors import SubscriptionNotFoundError
from app.services.tenant.tenant_lifecycle_service import TenantLifecycleService


class _Settings:
    def __init__(self, *, enable_billing: bool) -> None:
        self.enable_billing = enable_billing


def _account(tenant_id: UUID, status: TenantAccountStatus) -> TenantAccount:
    now = datetime.now(UTC)
    return TenantAccount(
        id=tenant_id,
        slug=f"tenant-{tenant_id.hex[:8]}",
        name="Acme Corp",
        status=status,
        created_at=now,
        updated_at=now,
        status_updated_at=now,
        status_updated_by=None,
        status_reason=None,
        suspended_at=now if status == TenantAccountStatus.SUSPENDED else None,
        deprovisioned_at=now if status == TenantAccountStatus.DEPROVISIONED else None,
    )


@pytest.mark.asyncio
async def test_deprovision_cancels_billing_and_finalizes() -> None:
    tenant_id = uuid4()
    tenant_service = AsyncMock()
    tenant_service.get_account = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.ACTIVE)
    )
    tenant_service.begin_deprovision = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.DEPROVISIONING)
    )
    tenant_service.finalize_deprovision = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.DEPROVISIONED)
    )
    billing_service = AsyncMock()
    billing_service.cancel_subscription = AsyncMock()

    service = TenantLifecycleService(
        tenant_account_service=tenant_service,
        billing_service=billing_service,
        settings_factory=lambda: cast(Settings, _Settings(enable_billing=True)),
        clock=lambda: datetime(2025, 1, 1, tzinfo=UTC),
    )

    await service.deprovision_tenant(
        tenant_id,
        actor_user_id=uuid4(),
        actor_role="platform_operator",
        reason="shutdown",
    )

    tenant_service.begin_deprovision.assert_awaited_once()
    billing_service.cancel_subscription.assert_awaited_once_with(
        str(tenant_id), cancel_at_period_end=False
    )
    tenant_service.finalize_deprovision.assert_awaited_once()


@pytest.mark.asyncio
async def test_deprovision_skips_billing_when_disabled() -> None:
    tenant_id = uuid4()
    tenant_service = AsyncMock()
    tenant_service.get_account = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.ACTIVE)
    )
    tenant_service.begin_deprovision = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.DEPROVISIONING)
    )
    tenant_service.finalize_deprovision = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.DEPROVISIONED)
    )
    billing_service = AsyncMock()

    service = TenantLifecycleService(
        tenant_account_service=tenant_service,
        billing_service=billing_service,
        settings_factory=lambda: cast(Settings, _Settings(enable_billing=False)),
        clock=lambda: datetime(2025, 1, 1, tzinfo=UTC),
    )

    await service.deprovision_tenant(
        tenant_id,
        actor_user_id=None,
        actor_role=None,
        reason=None,
    )

    billing_service.cancel_subscription.assert_not_called()
    tenant_service.finalize_deprovision.assert_awaited_once()


@pytest.mark.asyncio
async def test_deprovision_ignores_missing_subscription() -> None:
    tenant_id = uuid4()
    tenant_service = AsyncMock()
    tenant_service.get_account = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.ACTIVE)
    )
    tenant_service.begin_deprovision = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.DEPROVISIONING)
    )
    tenant_service.finalize_deprovision = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.DEPROVISIONED)
    )
    billing_service = AsyncMock()
    billing_service.cancel_subscription = AsyncMock(
        side_effect=SubscriptionNotFoundError("missing")
    )

    service = TenantLifecycleService(
        tenant_account_service=tenant_service,
        billing_service=billing_service,
        settings_factory=lambda: cast(Settings, _Settings(enable_billing=True)),
        clock=lambda: datetime(2025, 1, 1, tzinfo=UTC),
    )

    await service.deprovision_tenant(
        tenant_id,
        actor_user_id=None,
        actor_role=None,
        reason=None,
    )

    tenant_service.finalize_deprovision.assert_awaited_once()
