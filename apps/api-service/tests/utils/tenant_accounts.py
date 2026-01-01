from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.tenant_accounts import (
    TenantAccount,
    TenantAccountCreate,
    TenantAccountListResult,
    TenantAccountStatus,
    TenantAccountStatusUpdate,
    TenantAccountUpdate,
)


class StubTenantAccountRepository:
    def __init__(
        self,
        *,
        auto_create: bool = True,
        default_status: TenantAccountStatus = TenantAccountStatus.ACTIVE,
    ) -> None:
        self._auto_create = auto_create
        self._default_status = default_status
        self._accounts: dict[UUID, TenantAccount] = {}

    async def get(self, tenant_id: UUID) -> TenantAccount | None:
        account = self._accounts.get(tenant_id)
        if account is not None or not self._auto_create:
            return account
        account = self._build_account(
            tenant_id=tenant_id,
            name=f"Tenant {tenant_id.hex[:8]}",
            slug=f"tenant-{tenant_id.hex[:8]}",
            status=self._default_status,
        )
        self._accounts[tenant_id] = account
        return account

    async def get_by_slug(self, slug: str) -> TenantAccount | None:
        for account in self._accounts.values():
            if account.slug == slug:
                return account
        return None

    async def get_name(self, tenant_id: UUID) -> str | None:
        account = self._accounts.get(tenant_id)
        return account.name if account else None

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        status: TenantAccountStatus | None = None,
        query: str | None = None,
    ) -> TenantAccountListResult:
        accounts = list(self._accounts.values())
        if status is not None:
            accounts = [acct for acct in accounts if acct.status == status]
        if query:
            lowered = query.lower()
            accounts = [
                acct
                for acct in accounts
                if lowered in acct.name.lower() or lowered in acct.slug.lower()
            ]
        total = len(accounts)
        return TenantAccountListResult(
            accounts=accounts[offset : offset + limit],
            total=total,
        )

    async def create(self, payload: TenantAccountCreate) -> TenantAccount:
        tenant_id = payload.account_id or uuid4()
        now = datetime.now(UTC)
        account = TenantAccount(
            id=tenant_id,
            slug=payload.slug,
            name=payload.name,
            status=payload.status,
            created_at=now,
            updated_at=now,
            status_updated_at=now if payload.status else None,
            status_updated_by=payload.status_updated_by,
            status_reason=payload.status_reason,
            suspended_at=now if payload.status == TenantAccountStatus.SUSPENDED else None,
            deprovisioned_at=(
                now if payload.status == TenantAccountStatus.DEPROVISIONED else None
            ),
        )
        self._accounts[tenant_id] = account
        return account

    async def update(
        self, tenant_id: UUID, update: TenantAccountUpdate
    ) -> TenantAccount | None:
        account = await self.get(tenant_id)
        if account is None:
            return None
        name = update.name if update.name is not None else account.name
        slug = update.slug if update.slug is not None else account.slug
        now = datetime.now(UTC)
        updated = TenantAccount(
            id=account.id,
            slug=slug,
            name=name,
            status=account.status,
            created_at=account.created_at,
            updated_at=now,
            status_updated_at=account.status_updated_at,
            status_updated_by=account.status_updated_by,
            status_reason=account.status_reason,
            suspended_at=account.suspended_at,
            deprovisioned_at=account.deprovisioned_at,
        )
        self._accounts[tenant_id] = updated
        return updated

    async def update_status(
        self, tenant_id: UUID, update: TenantAccountStatusUpdate
    ) -> TenantAccount | None:
        account = await self.get(tenant_id)
        if account is None:
            return None
        updated = TenantAccount(
            id=account.id,
            slug=account.slug,
            name=account.name,
            status=update.status,
            created_at=account.created_at,
            updated_at=update.occurred_at,
            status_updated_at=update.occurred_at,
            status_updated_by=update.updated_by,
            status_reason=update.reason,
            suspended_at=update.suspended_at or account.suspended_at,
            deprovisioned_at=update.deprovisioned_at or account.deprovisioned_at,
        )
        self._accounts[tenant_id] = updated
        return updated

    def _build_account(
        self,
        *,
        tenant_id: UUID,
        name: str,
        slug: str,
        status: TenantAccountStatus,
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


__all__ = ["StubTenantAccountRepository"]
