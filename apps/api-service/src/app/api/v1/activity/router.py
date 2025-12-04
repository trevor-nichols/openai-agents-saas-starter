"""Activity log API surface."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.dependencies.tenant import TenantContext, get_tenant_context
from app.api.v1.activity.schemas import (
    ActivityEventItem,
    ActivityListResponse,
    ReceiptResponse,
)
from app.domain.activity import ActivityEventFilters
from app.services.activity import activity_service
from app.services.activity.service import (
    ActivityLookupError,
    ActivityNotFoundError,
    InvalidActivityIdError,
)

router = APIRouter(tags=["activity"], prefix="/activity")


@router.get("", response_model=ActivityListResponse)
async def list_activity_events(
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None, description="Opaque pagination cursor"),
    action: str | None = Query(None, description="Filter by action name"),
    actor_id: str | None = Query(None, description="Filter by actor id"),
    object_type: str | None = Query(None, description="Filter by object type"),
    object_id: str | None = Query(None, description="Filter by object id"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    request_id: str | None = Query(None, description="Filter by request id"),
    created_after: datetime | None = Query(None),
    created_before: datetime | None = Query(None),
    current_user: CurrentUser = Depends(require_verified_scopes("activity:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
) -> ActivityListResponse:
    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
    )

    filters = ActivityEventFilters(
        action=action,
        actor_id=actor_id,
        object_type=object_type,
        object_id=object_id,
        status=status_filter,  # type: ignore[arg-type]
        request_id=request_id,
        created_after=created_after,
        created_before=created_before,
    )

    user_id = _get_user_id(current_user)
    page = await activity_service.list_events_with_state(
        tenant_context.tenant_id,
        user_id,
        limit=limit,
        cursor=cursor,
        filters=filters,
    )

    items = [
        ActivityEventItem(
            id=item.id,
            tenant_id=item.tenant_id,
            action=item.action,
            created_at=item.created_at,
            actor_id=item.actor_id,
            actor_type=item.actor_type,
            actor_role=item.actor_role,
            object_type=item.object_type,
            object_id=item.object_id,
            object_name=item.object_name,
            status=item.status,
            source=item.source,
            request_id=item.request_id,
            ip_hash=item.ip_hash,
            user_agent=item.user_agent,
            metadata=dict(item.metadata) if item.metadata else None,
            read_state=item.read_state,
        )
        for item in page.items
    ]
    return ActivityListResponse(
        items=items,
        next_cursor=page.next_cursor,
        unread_count=page.unread_count,
    )


@router.get("/stream")
async def stream_activity_events(
    current_user: CurrentUser = Depends(require_verified_scopes("activity:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
) -> StreamingResponse:
    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
    )

    try:
        stream = await activity_service.subscribe(tenant_context.tenant_id)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    async def event_source() -> AsyncIterator[bytes]:
        try:
            while True:
                message = await stream.next_message(timeout=15)
                if message is None:
                    yield b":\n\n"
                    continue
                payload = f"data: {message}\n\n"
                yield payload.encode("utf-8")
        finally:
            await stream.close()

    return StreamingResponse(event_source(), media_type="text/event-stream")


@router.post("/{event_id}/read", response_model=ReceiptResponse)
async def mark_activity_read(
    event_id: str,
    current_user: CurrentUser = Depends(require_verified_scopes("activity:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
) -> ReceiptResponse:
    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
    )
    user_id = _get_user_id(current_user)
    try:
        await activity_service.mark_read(
            tenant_id=tenant_context.tenant_id,
            user_id=user_id,
            event_id=event_id,
        )
    except InvalidActivityIdError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ActivityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    try:
        unread = await activity_service.list_events_with_state(
            tenant_context.tenant_id,
            user_id,
            limit=1,
            cursor=None,
        )
        return ReceiptResponse(unread_count=unread.unread_count)
    except ActivityLookupError as exc:  # defensive, should not happen after mark
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{event_id}/dismiss", response_model=ReceiptResponse)
async def dismiss_activity(
    event_id: str,
    current_user: CurrentUser = Depends(require_verified_scopes("activity:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
) -> ReceiptResponse:
    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
    )
    user_id = _get_user_id(current_user)
    try:
        await activity_service.dismiss(
            tenant_id=tenant_context.tenant_id,
            user_id=user_id,
            event_id=event_id,
        )
    except InvalidActivityIdError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ActivityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    try:
        unread = await activity_service.list_events_with_state(
            tenant_context.tenant_id,
            user_id,
            limit=1,
            cursor=None,
        )
        return ReceiptResponse(unread_count=unread.unread_count)
    except ActivityLookupError as exc:  # defensive
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/mark-all-read", response_model=ReceiptResponse)
async def mark_all_activity_read(
    current_user: CurrentUser = Depends(require_verified_scopes("activity:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
) -> ReceiptResponse:
    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
    )
    await activity_service.mark_all_read(
        tenant_id=tenant_context.tenant_id,
        user_id=_get_user_id(current_user),
    )
    return ReceiptResponse(unread_count=0)


async def _resolve_tenant_context(
    current_user: CurrentUser,
    tenant_id_header: str | None,
    tenant_role_header: str | None,
) -> TenantContext:
    return await get_tenant_context(
        tenant_id_header=tenant_id_header,
        tenant_role_header=tenant_role_header,
        current_user=current_user,
    )


def _get_user_id(current_user: CurrentUser) -> str:
    candidate = (
        current_user.get("user_id")
        or current_user.get("subject")
        or (current_user.get("payload") or {}).get("sub")
    )
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to resolve current user id for activity inbox.",
        )
    return str(candidate)
