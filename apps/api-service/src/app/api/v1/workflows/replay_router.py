"""Workflow run replay endpoints (public_sse_v1 ledger frames)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.dependencies.tenant import TenantContext
from app.api.v1.workflows.dependencies import require_workflow_viewer_role
from app.api.v1.workflows.schemas import WorkflowRunReplayEventsResponse
from app.domain.conversations import ConversationNotFoundError
from app.services.conversations.ledger_reader import get_conversation_ledger_reader
from app.services.workflows.service import get_workflow_service

router = APIRouter(prefix="/workflows/runs", tags=["workflows"])

RUN_REPLAY_STREAM_RESPONSE = {
    "description": (
        "Server-sent events replay stream of persisted public_sse_v1 frames for a workflow run."
    ),
    "content": {
        "text/event-stream": {
            "schema": {"type": "string"}
        }
    },
}


async def _resolve_run_conversation_or_404(
    *,
    run_id: str,
    tenant_context: TenantContext,
) -> str:
    service = get_workflow_service()
    try:
        run, _steps = await service.get_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if run.tenant_id != tenant_context.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")

    conversation_id = (run.conversation_id or "").strip()
    if not conversation_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workflow run is missing conversation linkage",
        )
    return conversation_id


@router.get(
    "/{run_id}/replay/events",
    response_model=WorkflowRunReplayEventsResponse,
)
async def get_workflow_run_replay_events(
    run_id: str,
    _current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_context: TenantContext = Depends(require_workflow_viewer_role),
    limit: int = Query(500, ge=1, le=1000),
    cursor: str | None = Query(None, description="Opaque pagination cursor."),
) -> WorkflowRunReplayEventsResponse:
    """Return persisted public_sse_v1 frames for deterministic workflow run UI replay."""

    conversation_id = await _resolve_run_conversation_or_404(
        run_id=run_id, tenant_context=tenant_context
    )

    try:
        events, next_cursor = await get_conversation_ledger_reader().get_events_page(
            tenant_id=tenant_context.tenant_id,
            conversation_id=conversation_id,
            workflow_run_id=run_id,
            limit=limit,
            cursor=cursor,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return WorkflowRunReplayEventsResponse(
        workflow_run_id=run_id,
        conversation_id=conversation_id,
        items=events,
        next_cursor=next_cursor,
    )


@router.get(
    "/{run_id}/replay/stream",
    responses={200: RUN_REPLAY_STREAM_RESPONSE},
)
async def stream_workflow_run_replay_events(
    run_id: str,
    _current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_context: TenantContext = Depends(require_workflow_viewer_role),
    cursor: str | None = Query(None, description="Opaque pagination cursor."),
) -> StreamingResponse:
    """SSE replay of persisted public_sse_v1 frames for a workflow run (exactly as emitted)."""

    conversation_id = await _resolve_run_conversation_or_404(
        run_id=run_id, tenant_context=tenant_context
    )

    reader = get_conversation_ledger_reader()
    store = reader.store
    if store is None:  # pragma: no cover - defensive
        raise RuntimeError("ConversationLedgerQueryStore is not configured")

    # Preflight cursor validity before streaming starts, so we can return proper HTTP errors
    # instead of failing mid-stream.
    try:
        await store.list_events_page(
            conversation_id,
            tenant_id=tenant_context.tenant_id,
            limit=1,
            cursor=cursor,
            workflow_run_id=run_id,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    async def _event_stream() -> AsyncIterator[str]:
        async for payload in reader.iter_events_json(
            tenant_id=tenant_context.tenant_id,
            conversation_id=conversation_id,
            workflow_run_id=run_id,
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
