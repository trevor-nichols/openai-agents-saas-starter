"""Chat-related API endpoints."""

import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import raise_rate_limit_http_error
from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.v1.chat.schemas import AgentChatRequest, AgentChatResponse, StreamingChatResponse
from app.core.config import get_settings
from app.services.agent_service import agent_service
from app.services.rate_limit_service import (
    ConcurrencyQuota,
    RateLimitExceeded,
    RateLimitLease,
    RateLimitQuota,
    rate_limiter,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=AgentChatResponse)
async def chat_with_agent(
    request: AgentChatRequest,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:write")),
) -> AgentChatResponse:
    """Send a message to the agent framework and receive a full response."""

    settings = get_settings()
    await _enforce_user_quota(
        quota=RateLimitQuota(
            name="chat_per_minute",
            limit=settings.chat_rate_limit_per_minute,
            window_seconds=60,
            scope="user",
        ),
        user=current_user,
    )

    try:
        return await agent_service.chat(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {exc}",
        ) from exc


@router.post("/stream")
async def stream_chat_with_agent(
    request: AgentChatRequest,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:write")),
) -> StreamingResponse:
    """Provide an SSE stream for real-time agent responses."""

    settings = get_settings()
    await _enforce_user_quota(
        quota=RateLimitQuota(
            name="chat_stream_per_minute",
            limit=settings.chat_stream_rate_limit_per_minute,
            window_seconds=60,
            scope="user",
        ),
        user=current_user,
    )
    stream_lease = await _acquire_stream_slot(
        quota=ConcurrencyQuota(
            name="chat_stream_concurrency",
            limit=settings.chat_stream_concurrent_limit,
            ttl_seconds=300,
            scope="user",
        ),
        user=current_user,
    )

    async def _event_stream() -> AsyncIterator[str]:
        async with stream_lease:
            try:
                async for chunk in agent_service.chat_stream(request):
                    payload = StreamingChatResponse(
                        chunk=chunk.chunk,
                        conversation_id=chunk.conversation_id,
                        is_complete=chunk.is_complete,
                        agent_used=chunk.agent_used,
                    )
                    yield f"data: {payload.model_dump_json()}\n\n"

                    if payload.is_complete:
                        break
            except Exception as exc:
                error_payload = {
                    "error": str(exc),
                    "conversation_id": request.conversation_id or "unknown",
                    "is_complete": True,
                    "chunk": "",
                }
                yield f"data: {json.dumps(error_payload)}\n\n"

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


async def _enforce_user_quota(quota: RateLimitQuota, user: CurrentUser) -> None:
    tenant_id, user_id = _user_identity(user)
    if quota.limit <= 0:
        return
    try:
        await rate_limiter.enforce(quota, [tenant_id, user_id])
    except RateLimitExceeded as exc:
        raise_rate_limit_http_error(exc, tenant_id=tenant_id, user_id=user_id)


async def _acquire_stream_slot(quota: ConcurrencyQuota, user: CurrentUser) -> RateLimitLease:
    tenant_id, user_id = _user_identity(user)
    if quota.limit <= 0:
        return RateLimitLease(None, None)
    try:
        return await rate_limiter.acquire_concurrency(quota, [tenant_id, user_id])
    except RateLimitExceeded as exc:
        raise_rate_limit_http_error(exc, tenant_id=tenant_id, user_id=user_id)


def _user_identity(user: CurrentUser) -> tuple[str, str]:
    payload_obj = user.get("payload") if isinstance(user, dict) else None
    payload: dict[str, Any] | None
    if isinstance(payload_obj, dict):
        payload = payload_obj
    else:
        payload = None
    tenant_id = str((payload or {}).get("tenant_id") or "unknown")
    user_id = str(user.get("user_id") or "anonymous")
    return tenant_id, user_id
