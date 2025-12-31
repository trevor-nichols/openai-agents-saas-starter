"""Tenant account domain models and repository contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol
from uuid import UUID


class TenantAccountStatus(str, Enum):
    """Lifecycle states for tenant accounts."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEPROVISIONING = "deprovisioning"
    DEPROVISIONED = "deprovisioned"


@dataclass(slots=True)
class TenantAccount:
    id: UUID
    slug: str
    name: str
    status: TenantAccountStatus
    created_at: datetime
    updated_at: datetime
    status_updated_at: datetime | None = None
    status_updated_by: UUID | None = None
    status_reason: str | None = None
    suspended_at: datetime | None = None
    deprovisioned_at: datetime | None = None


@dataclass(slots=True)
class TenantAccountCreate:
    name: str
    slug: str
    status: TenantAccountStatus = TenantAccountStatus.ACTIVE
    account_id: UUID | None = None
    status_updated_by: UUID | None = None
    status_reason: str | None = None


@dataclass(slots=True)
class TenantAccountUpdate:
    name: str | None = None
    slug: str | None = None


@dataclass(slots=True)
class TenantAccountStatusUpdate:
    status: TenantAccountStatus
    occurred_at: datetime
    updated_by: UUID | None = None
    reason: str | None = None
    suspended_at: datetime | None = None
    deprovisioned_at: datetime | None = None


@dataclass(slots=True)
class TenantAccountListResult:
    accounts: list[TenantAccount]
    total: int


class TenantAccountRepository(Protocol):
    async def get(self, tenant_id: UUID) -> TenantAccount | None: ...

    async def get_by_slug(self, slug: str) -> TenantAccount | None: ...

    async def get_name(self, tenant_id: UUID) -> str | None: ...

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        status: TenantAccountStatus | None = None,
        query: str | None = None,
    ) -> TenantAccountListResult: ...

    async def create(self, payload: TenantAccountCreate) -> TenantAccount: ...

    async def update(
        self, tenant_id: UUID, update: TenantAccountUpdate
    ) -> TenantAccount | None: ...

    async def update_status(
        self, tenant_id: UUID, update: TenantAccountStatusUpdate
    ) -> TenantAccount | None: ...


class TenantAccountRepositoryError(RuntimeError):
    """Base error for tenant account persistence operations."""


class TenantAccountSlugConflictError(TenantAccountRepositoryError):
    """Raised when a tenant slug conflicts with an existing record."""


__all__ = [
    "TenantAccount",
    "TenantAccountCreate",
    "TenantAccountListResult",
    "TenantAccountRepository",
    "TenantAccountRepositoryError",
    "TenantAccountSlugConflictError",
    "TenantAccountStatus",
    "TenantAccountStatusUpdate",
    "TenantAccountUpdate",
]
