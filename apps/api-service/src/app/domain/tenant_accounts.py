"""Tenant account domain ports."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID


class TenantAccountRepository(Protocol):
    async def get_name(self, tenant_id: UUID) -> str | None: ...


__all__ = ["TenantAccountRepository"]
