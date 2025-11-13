"""Domain entities and repository contracts for tenant settings."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class BillingContact:
    """Represents a single billing contact for a tenant."""

    name: str
    email: str
    role: str | None = None
    phone: str | None = None
    notify_billing: bool = True


@dataclass(slots=True)
class TenantSettingsSnapshot:
    """Full snapshot of mutable tenant configuration."""

    tenant_id: str
    billing_contacts: list[BillingContact] = field(default_factory=list)
    billing_webhook_url: str | None = None
    plan_metadata: dict[str, str] = field(default_factory=dict)
    flags: dict[str, bool] = field(default_factory=dict)
    updated_at: datetime | None = None


class TenantSettingsRepository(Protocol):
    """Persistence contract for tenant configuration documents."""

    async def fetch(self, tenant_id: str) -> TenantSettingsSnapshot | None: ...

    async def upsert(
        self,
        tenant_id: str,
        *,
        billing_contacts: list[BillingContact],
        billing_webhook_url: str | None,
        plan_metadata: dict[str, str],
        flags: dict[str, bool],
    ) -> TenantSettingsSnapshot: ...


__all__ = [
    "BillingContact",
    "TenantSettingsSnapshot",
    "TenantSettingsRepository",
]
