"""Unit tests for tenant account service."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.domain.tenant_accounts import (
    TenantAccount,
    TenantAccountSlugConflictError,
    TenantAccountStatus,
)
from app.services.tenant.tenant_account_service import (
    TenantAccountSlugCollisionError,
    TenantAccountService,
    TenantAccountStatusError,
    TenantAccountValidationError,
)


def _account(
    tenant_id: UUID,
    status: TenantAccountStatus,
    *,
    slug: str = "acme",
    name: str = "Acme Corp",
) -> TenantAccount:
    now = datetime.now(UTC)
    return TenantAccount(
        id=tenant_id,
        slug=slug,
        name=name,
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
async def test_create_account_generates_slug_and_persists() -> None:
    repository = AsyncMock()
    repository.get_by_slug = AsyncMock(return_value=None)
    created = _account(uuid4(), TenantAccountStatus.ACTIVE, slug="acme-co")
    repository.create = AsyncMock(return_value=created)
    service = TenantAccountService(
        repository=repository,
        slug_generator=lambda _: "acme-co",
    )

    account = await service.create_account(name=" Acme Co ")

    assert account.slug == "acme-co"
    repository.get_by_slug.assert_awaited_once_with("acme-co")
    assert repository.create.await_count == 1
    await_args = repository.create.await_args
    assert await_args is not None
    payload = await_args.args[0]
    assert payload.slug == "acme-co"
    assert payload.name == "Acme Co"


@pytest.mark.asyncio
async def test_create_account_rejects_invalid_slug() -> None:
    repository = AsyncMock()
    service = TenantAccountService(repository=repository)

    with pytest.raises(TenantAccountValidationError):
        await service.create_account(name="Acme", slug="Bad Slug")

    assert repository.get_by_slug.await_count == 0


@pytest.mark.asyncio
async def test_create_account_maps_slug_conflict() -> None:
    repository = AsyncMock()
    repository.get_by_slug = AsyncMock(return_value=None)
    repository.create = AsyncMock(
        side_effect=TenantAccountSlugConflictError("Tenant slug already exists.")
    )
    service = TenantAccountService(repository=repository)

    with pytest.raises(TenantAccountSlugCollisionError):
        await service.create_account(name="Acme", slug="acme")


@pytest.mark.asyncio
async def test_update_account_rejects_slug_change_without_flag() -> None:
    repository = AsyncMock()
    service = TenantAccountService(repository=repository)

    with pytest.raises(TenantAccountValidationError):
        await service.update_account(uuid4(), slug="new-slug", allow_slug_change=False)

    assert repository.update.await_count == 0


@pytest.mark.asyncio
async def test_update_account_maps_slug_conflict() -> None:
    tenant_id = uuid4()
    repository = AsyncMock()
    repository.get_by_slug = AsyncMock(return_value=None)
    repository.update = AsyncMock(
        side_effect=TenantAccountSlugConflictError("Tenant slug already exists.")
    )
    service = TenantAccountService(repository=repository)

    with pytest.raises(TenantAccountSlugCollisionError):
        await service.update_account(
            tenant_id,
            name="Acme",
            slug="acme",
            allow_slug_change=True,
        )

    assert repository.update.await_count == 1


@pytest.mark.asyncio
async def test_suspend_account_updates_status() -> None:
    tenant_id = uuid4()
    repository = AsyncMock()
    repository.get = AsyncMock(return_value=_account(tenant_id, TenantAccountStatus.ACTIVE))
    now = datetime(2025, 1, 1, tzinfo=UTC)
    repository.update_status = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.SUSPENDED)
    )
    service = TenantAccountService(repository=repository, clock=lambda: now)

    account = await service.suspend_account(
        tenant_id, actor_user_id=uuid4(), reason="policy"
    )

    assert account.status == TenantAccountStatus.SUSPENDED
    await_args = repository.update_status.await_args
    assert await_args is not None
    update = await_args.args[1]
    assert update.status == TenantAccountStatus.SUSPENDED
    assert update.suspended_at == now


@pytest.mark.asyncio
async def test_complete_provisioning_updates_status() -> None:
    tenant_id = uuid4()
    repository = AsyncMock()
    repository.get = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.PROVISIONING)
    )
    now = datetime(2025, 1, 1, tzinfo=UTC)
    repository.update_status = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.ACTIVE)
    )
    service = TenantAccountService(repository=repository, clock=lambda: now)

    account = await service.complete_provisioning(
        tenant_id, actor_user_id=uuid4(), reason="signup"
    )

    assert account.status == TenantAccountStatus.ACTIVE
    await_args = repository.update_status.await_args
    assert await_args is not None
    update = await_args.args[1]
    assert update.status == TenantAccountStatus.ACTIVE


@pytest.mark.asyncio
async def test_reactivate_rejects_invalid_transition() -> None:
    tenant_id = uuid4()
    repository = AsyncMock()
    repository.get = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.DEPROVISIONING)
    )
    service = TenantAccountService(repository=repository)

    with pytest.raises(TenantAccountStatusError):
        await service.reactivate_account(tenant_id, actor_user_id=None, reason=None)


@pytest.mark.asyncio
async def test_finalize_deprovision_requires_deprovisioning_state() -> None:
    tenant_id = uuid4()
    repository = AsyncMock()
    repository.get = AsyncMock(
        return_value=_account(tenant_id, TenantAccountStatus.ACTIVE)
    )
    service = TenantAccountService(repository=repository)

    with pytest.raises(TenantAccountStatusError):
        await service.finalize_deprovision(
            tenant_id,
            actor_user_id=None,
            reason=None,
        )

    assert repository.update_status.await_count == 0
