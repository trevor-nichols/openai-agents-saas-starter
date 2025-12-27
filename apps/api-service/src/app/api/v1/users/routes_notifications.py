"""Notification preference CRUD endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import require_current_user
from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.models.notifications import (
    NotificationPreferenceRequest,
    NotificationPreferenceView,
)
from app.services.notification_preferences import (
    NotificationPreferenceService,
    get_notification_preference_service,
)

router = APIRouter(prefix="/users", tags=["users"])


def _service() -> NotificationPreferenceService:
    return get_notification_preference_service()


_ALLOWED_VIEWER_ROLES: tuple[TenantRole, ...] = (
    TenantRole.VIEWER,
    TenantRole.ADMIN,
    TenantRole.OWNER,
)


@router.put("/notification-preferences", response_model=NotificationPreferenceView)
async def upsert_notification_preference(
    payload: NotificationPreferenceRequest,
    current_user: dict[str, str] = Depends(require_current_user),
    context: TenantContext = Depends(require_tenant_role(*_ALLOWED_VIEWER_ROLES)),
) -> NotificationPreferenceView:
    tenant_id = payload.tenant_id or UUID(context.tenant_id)
    if payload.tenant_id and payload.tenant_id != UUID(context.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context mismatch for notification preferences.",
        )
    service = _service()
    pref = await service.upsert_preference(
        user_id=UUID(current_user["user_id"]),
        channel=payload.channel,
        category=payload.category,
        enabled=payload.enabled,
        tenant_id=tenant_id,
    )
    return NotificationPreferenceView(
        id=pref.id,
        channel=pref.channel,
        category=pref.category,
        enabled=pref.enabled,
        tenant_id=pref.tenant_id,
    )


@router.get("/notification-preferences", response_model=list[NotificationPreferenceView])
async def list_notification_preferences(
    current_user: dict[str, str] = Depends(require_current_user),
    context: TenantContext = Depends(require_tenant_role(*_ALLOWED_VIEWER_ROLES)),
) -> list[NotificationPreferenceView]:
    service = _service()
    prefs = await service.list_preferences(
        user_id=UUID(current_user["user_id"]), tenant_id=UUID(context.tenant_id)
    )
    return [
        NotificationPreferenceView(
            id=p.id,
            channel=p.channel,
            category=p.category,
            enabled=p.enabled,
            tenant_id=p.tenant_id,
        )
        for p in prefs
    ]
