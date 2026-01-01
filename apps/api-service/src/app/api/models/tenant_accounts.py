"""Tenant account request and response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.tenant_accounts import TenantAccount, TenantAccountStatus


class TenantAccountResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    slug: str
    name: str
    status: TenantAccountStatus
    created_at: datetime
    updated_at: datetime
    status_updated_at: datetime | None = None
    suspended_at: datetime | None = None
    deprovisioned_at: datetime | None = None

    @classmethod
    def from_domain(cls, account: TenantAccount) -> TenantAccountResponse:
        return cls(
            id=account.id,
            slug=account.slug,
            name=account.name,
            status=account.status,
            created_at=account.created_at,
            updated_at=account.updated_at,
            status_updated_at=account.status_updated_at,
            suspended_at=account.suspended_at,
            deprovisioned_at=account.deprovisioned_at,
        )


class TenantAccountOperatorResponse(TenantAccountResponse):
    status_reason: str | None = None
    status_updated_by: UUID | None = None

    @classmethod
    def from_domain(cls, account: TenantAccount) -> TenantAccountOperatorResponse:
        base = TenantAccountResponse.from_domain(account)
        return cls(
            **base.model_dump(),
            status_reason=account.status_reason,
            status_updated_by=account.status_updated_by,
        )


class TenantAccountListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accounts: list[TenantAccountOperatorResponse]
    total: int


class TenantAccountCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=128)
    slug: str | None = Field(default=None, max_length=64)


class TenantAccountUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=128)
    slug: str | None = Field(default=None, max_length=64)


class TenantAccountSelfUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=128)


class TenantAccountLifecycleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=3, max_length=256)


__all__ = [
    "TenantAccountCreateRequest",
    "TenantAccountLifecycleRequest",
    "TenantAccountListResponse",
    "TenantAccountOperatorResponse",
    "TenantAccountResponse",
    "TenantAccountSelfUpdateRequest",
    "TenantAccountUpdateRequest",
]
