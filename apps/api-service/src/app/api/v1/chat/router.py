"""Chat-related API endpoints."""

import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from app.api.dependencies import raise_rate_limit_http_error
from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.dependencies.usage import enforce_usage_guardrails
from app.api.v1.chat.schemas import (
    AgentChatRequest,
    AgentChatResponse,
    ContainerFileCitation,
    FileCitation,
    StreamingChatEvent,
    ToolCallPayload,
    UrlCitation,
)
from app.core.settings import get_settings
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

logger = logging.getLogger(__name__)


STREAM_EVENT_RESPONSE = {
    "description": "Server-sent events stream of agent outputs.",
    "model": StreamingChatEvent,
    "content": {
        "text/event-stream": {
            "schema": {"$ref": "#/components/schemas/StreamingChatEvent"}
        }
    },
}


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


@router.post("/stream", responses={200: STREAM_EVENT_RESPONSE})
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
                async for event in agent_service.chat_stream(request, actor=actor):
                    annotations: list[
                        UrlCitation | ContainerFileCitation | FileCitation
                    ] | None = None
                    if isinstance(event.annotations, list):
                        parsed: list[UrlCitation | ContainerFileCitation | FileCitation] = []
                        for ann in event.annotations:
                            if not isinstance(ann, dict):
                                continue
                            try:
                                parsed.append(UrlCitation.model_validate(ann))
                                continue
                            except Exception:
                                pass
                            try:
                                parsed.append(ContainerFileCitation.model_validate(ann))
                                continue
                            except Exception:
                                pass
                            try:
                                parsed.append(FileCitation.model_validate(ann))
                            except Exception:
                                continue
                        annotations = parsed or None

                    parsed_tool_call: ToolCallPayload | dict[str, Any] | None = None
                    try:
                        if isinstance(event.tool_call, dict):
                            parsed_tool_call = ToolCallPayload.model_validate(event.tool_call)
                    except ValidationError:
                        parsed_tool_call = event.tool_call if isinstance(event.tool_call, dict) else None

                    payload = StreamingChatEvent(
                        kind=event.kind,
                        conversation_id=event.conversation_id or request.conversation_id or "",
                        agent_used=event.agent,
                        response_id=event.response_id,
                        sequence_number=event.sequence_number,
                        raw_type=event.raw_type,
                        run_item_name=event.run_item_name,
                        run_item_type=event.run_item_type,
                        tool_call_id=event.tool_call_id,
                        tool_name=event.tool_name,
                        agent=event.agent,
                        new_agent=event.new_agent,
                        text_delta=event.text_delta,
                        reasoning_delta=event.reasoning_delta,
                        response_text=event.response_text,
                        structured_output=event.structured_output,
                        is_terminal=event.is_terminal,
                        payload=event.payload if isinstance(event.payload, dict) else None,
                        attachments=event.attachments,
                        raw_event=event.raw_event if isinstance(event.raw_event, dict) else None,
                        tool_call=parsed_tool_call,
                        annotations=annotations,
                    )

                    yield f"data: {payload.model_dump_json()}\n\n"

                    if event.is_terminal:
                        # Allow the upstream generator to finish naturally so
                        # downstream cleanup (session sync, persistence) runs.
                        # The generator will end on its own after emitting the
                        # terminal event.
                        continue
            except Exception as exc:
                logger.exception(
                    "chat.stream.serialization_error",
                    extra={
                        "conversation_id": request.conversation_id,
                        "agent": request.agent_type,
                        "error": str(exc),
                    },
                )
                error_payload = StreamingChatEvent(
                    kind="error",
                    conversation_id=request.conversation_id or "unknown",
                    agent_used=None,
                    response_id=None,
                    sequence_number=None,
                    raw_type=None,
                    run_item_name=None,
                    run_item_type=None,
                    tool_call_id=None,
                    tool_name=None,
                    agent=None,
                    new_agent=None,
                    text_delta=None,
                    reasoning_delta=None,
                    is_terminal=True,
                    payload={"error": str(exc)},
                )
                yield f"data: {error_payload.model_dump_json()}\n\n"

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
