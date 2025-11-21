"""Chat-related API endpoints."""

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import raise_rate_limit_http_error
from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.dependencies.usage import enforce_usage_guardrails
from app.api.v1.chat.schemas import AgentChatRequest, AgentChatResponse, StreamingChatResponse
from app.core.config import get_settings
from app.services.agent_service import ConversationActorContext, agent_service
from app.services.shared.rate_limit_service import (
    ConcurrencyQuota,
    RateLimitExceeded,
    RateLimitLease,
    RateLimitQuota,
    rate_limiter,
)

router = APIRouter(prefix="/chat", tags=["chat"])
_ALLOWED_VIEWER_ROLES: tuple[TenantRole, ...] = (
    TenantRole.VIEWER,
    TenantRole.ADMIN,
    TenantRole.OWNER,
)


@router.post("", response_model=AgentChatResponse)
async def chat_with_agent(
    request: AgentChatRequest,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:write")),
    tenant_context: TenantContext = Depends(require_tenant_role(*_ALLOWED_VIEWER_ROLES)),
    _: object = Depends(enforce_usage_guardrails),
) -> AgentChatResponse:
    """Send a message to the agent framework and receive a full response."""

    actor = _conversation_actor(current_user, tenant_context)
    settings = get_settings()
    await _enforce_user_quota(
        quota=RateLimitQuota(
            name="chat_per_minute",
            limit=settings.chat_rate_limit_per_minute,
            window_seconds=60,
            scope="user",
        ),
        tenant_id=tenant_context.tenant_id,
        user_id=actor.user_id,
    )

    try:
        return await agent_service.chat(request, actor=actor)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {exc}",
        ) from exc


@router.post("/stream")
async def stream_chat_with_agent(
    request: AgentChatRequest,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:write")),
    tenant_context: TenantContext = Depends(require_tenant_role(*_ALLOWED_VIEWER_ROLES)),
    _: object = Depends(enforce_usage_guardrails),
) -> StreamingResponse:
    """Provide an SSE stream for real-time agent responses."""

    actor = _conversation_actor(current_user, tenant_context)
    settings = get_settings()
    await _enforce_user_quota(
        quota=RateLimitQuota(
            name="chat_stream_per_minute",
            limit=settings.chat_stream_rate_limit_per_minute,
            window_seconds=60,
            scope="user",
        ),
        tenant_id=tenant_context.tenant_id,
        user_id=actor.user_id,
    )
    stream_lease = await _acquire_stream_slot(
        quota=ConcurrencyQuota(
            name="chat_stream_concurrency",
            limit=settings.chat_stream_concurrent_limit,
            ttl_seconds=300,
            scope="user",
        ),
        tenant_id=tenant_context.tenant_id,
        user_id=actor.user_id,
    )

    async def _event_stream() -> AsyncIterator[str]:
        async with stream_lease:
            try:
                async for chunk in agent_service.chat_stream(request, actor=actor):
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


async def _enforce_user_quota(quota: RateLimitQuota, *, tenant_id: str, user_id: str) -> None:
    if quota.limit <= 0:
        return
    try:
        await rate_limiter.enforce(quota, [tenant_id, user_id])
    except RateLimitExceeded as exc:
        raise_rate_limit_http_error(exc, tenant_id=tenant_id, user_id=user_id)


async def _acquire_stream_slot(
    quota: ConcurrencyQuota, *, tenant_id: str, user_id: str
) -> RateLimitLease:
    if quota.limit <= 0:
        return RateLimitLease(None, None)
    try:
        return await rate_limiter.acquire_concurrency(quota, [tenant_id, user_id])
    except RateLimitExceeded as exc:
        raise_rate_limit_http_error(exc, tenant_id=tenant_id, user_id=user_id)


def _conversation_actor(
    current_user: CurrentUser, tenant_context: TenantContext
) -> ConversationActorContext:
    return ConversationActorContext(
        tenant_id=tenant_context.tenant_id,
        user_id=_user_id(current_user),
    )


def _user_id(user: CurrentUser) -> str:
    payload_obj = user.get("payload") if isinstance(user, dict) else None
    payload = payload_obj if isinstance(payload_obj, dict) else {}
    return str(user.get("user_id") or payload.get("sub") or "anonymous")
