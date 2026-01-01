"""Conversation ledger replay endpoints (public_sse_v1)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.dependencies.tenant import TenantRole
from app.api.v1.conversations.dependencies import resolve_tenant_context
from app.api.v1.conversations.schemas import ConversationLedgerEventsResponse
from app.domain.conversations import ConversationNotFoundError
from app.services.conversations.ledger_reader import get_conversation_ledger_reader

router = APIRouter(prefix="/conversations", tags=["conversations"])

LEDGER_STREAM_RESPONSE = {
    "description": "Server-sent events replay stream of persisted public_sse_v1 frames.",
    "content": {
        "text/event-stream": {
            "schema": {"type": "string"}
        }
    },
}


@router.get("/{conversation_id}/ledger/events", response_model=ConversationLedgerEventsResponse)
async def get_conversation_ledger_events(
    conversation_id: str,
    request: Request,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
    limit: int = Query(500, ge=1, le=1000),
    cursor: str | None = Query(None, description="Opaque pagination cursor."),
) -> ConversationLedgerEventsResponse:
    """Return persisted public_sse_v1 frames for deterministic UI replay."""

    tenant_context = await resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
        request=request,
        min_role=TenantRole.VIEWER,
    )

    try:
        events, next_cursor = await get_conversation_ledger_reader().get_events_page(
            tenant_id=tenant_context.tenant_id,
            conversation_id=conversation_id,
            limit=limit,
            cursor=cursor,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ConversationLedgerEventsResponse(
        conversation_id=conversation_id,
        items=events,
        next_cursor=next_cursor,
    )


@router.get(
    "/{conversation_id}/ledger/stream",
    responses={200: LEDGER_STREAM_RESPONSE},
)
async def stream_conversation_ledger_events(
    conversation_id: str,
    request: Request,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
    cursor: str | None = Query(None, description="Opaque pagination cursor."),
) -> StreamingResponse:
    """SSE replay of persisted public_sse_v1 frames (exactly as originally emitted)."""

    tenant_context = await resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
        request=request,
        min_role=TenantRole.VIEWER,
    )

    reader = get_conversation_ledger_reader()
    store = reader.store
    if store is None:  # pragma: no cover - defensive
        raise RuntimeError("ConversationLedgerQueryStore is not configured")

    # Preflight tenant/conversation access and cursor validity before streaming starts, so we
    # can return proper HTTP errors instead of failing mid-stream.
    try:
        await store.list_events_page(
            conversation_id,
            tenant_id=tenant_context.tenant_id,
            limit=1,
            cursor=cursor,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    async def _event_stream() -> AsyncIterator[str]:
        async for payload in reader.iter_events_json(
            tenant_id=tenant_context.tenant_id,
            conversation_id=conversation_id,
            cursor=cursor,
        ):
            yield f"data: {payload}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
    }

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers=headers,
    )


__all__ = ["router"]
