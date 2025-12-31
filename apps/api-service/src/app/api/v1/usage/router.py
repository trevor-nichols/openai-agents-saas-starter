"""Tenant usage counter read endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.models.usage import UsageCounterView
from app.services.usage.counters import UsageCounterService, get_usage_counter_service

router = APIRouter(prefix="/usage", tags=["usage"])


def _service() -> UsageCounterService:
    return get_usage_counter_service()


_ALLOWED_VIEWER_ROLES: tuple[TenantRole, ...] = (
    TenantRole.VIEWER,
    TenantRole.MEMBER,
    TenantRole.ADMIN,
    TenantRole.OWNER,
)


@router.get("", response_model=list[UsageCounterView])
async def list_usage(
    context: TenantContext = Depends(require_tenant_role(*_ALLOWED_VIEWER_ROLES)),
) -> list[UsageCounterView]:
    service = _service()
    counters = await service.list_for_tenant(
        tenant_id=UUID(context.tenant_id), limit=100  # generous default for dashboard
    )
    return [
        UsageCounterView(
            id=row.id,
            tenant_id=row.tenant_id,
            user_id=row.user_id if row.user_id is not None else None,
            period_start=row.period_start,
            granularity=row.granularity.value,
            input_tokens=row.input_tokens,
            output_tokens=row.output_tokens,
            requests=row.requests,
            storage_bytes=row.storage_bytes,
            updated_at=row.updated_at,
        )
        for row in counters
    ]
