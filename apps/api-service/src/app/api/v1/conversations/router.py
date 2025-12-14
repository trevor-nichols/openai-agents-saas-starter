"""Conversation management endpoints."""

from collections.abc import AsyncIterator
from typing import Literal, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.dependencies.tenant import TenantContext, TenantRole, get_tenant_context
from app.api.v1.chat.schemas import MessageAttachment
from app.api.v1.conversations.schemas import (
    ConversationEventItem,
    ConversationEventsResponse,
    ConversationHistory,
    ConversationListResponse,
    ConversationMemoryConfigRequest,
    ConversationMemoryConfigResponse,
    ConversationSearchResponse,
    ConversationSearchResult,
    ConversationTitleUpdateRequest,
    ConversationTitleUpdateResponse,
    PaginatedMessagesResponse,
)
from app.domain.conversations import ConversationMemoryConfig, ConversationNotFoundError
from app.services.agents.context import ConversationActorContext
from app.services.agents.query import get_conversation_query_service
from app.services.conversation_service import get_conversation_service
from app.services.conversations.title_service import get_title_service

router = APIRouter(prefix="/conversations", tags=["conversations"])

TITLE_STREAM_RESPONSE = {
    "description": "Server-sent events stream of the generated conversation title.",
    "content": {
        "text/event-stream": {
            "schema": {"type": "string"}
        }
    },
}


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None, description="Opaque pagination cursor."),
    agent: str | None = Query(None, description="Filter by agent entrypoint."),
) -> ConversationListResponse:
    """List stored conversations ordered by recency."""

    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
        min_role=TenantRole.VIEWER,
    )
    actor = _conversation_actor(current_user, tenant_context)
    try:
        summaries, next_cursor = await get_conversation_query_service().list_summaries(
            actor=actor,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent,
        )
    except ValueError as exc:  # e.g., malformed cursor
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return ConversationListResponse(items=summaries, next_cursor=next_cursor)


@router.get("/search", response_model=ConversationSearchResponse)
async def search_conversations(
    q: str = Query(..., min_length=1, description="Search query."),
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None, description="Opaque pagination cursor."),
    agent: str | None = Query(None, description="Filter by agent entrypoint."),
) -> ConversationSearchResponse:
    """Search conversations by message text."""

    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
        min_role=TenantRole.VIEWER,
    )
    actor = _conversation_actor(current_user, tenant_context)

    try:
        results, next_cursor = await get_conversation_query_service().search(
            actor=actor,
            query=q,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent,
        )
    except ValueError as exc:  # malformed cursor or query
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    response_items: list[ConversationSearchResult] = []
    for result in results:
        response_items.append(
            ConversationSearchResult(
                conversation_id=result.conversation_id,
                display_name=result.display_name,
                agent_entrypoint=result.agent_entrypoint,
                active_agent=result.active_agent,
                topic_hint=result.topic_hint,
                status=result.status,
                preview=result.preview,
                last_message_preview=result.last_message_preview,
                score=result.score,
                updated_at=result.updated_at.isoformat() if result.updated_at else None,
            )
        )

    return ConversationSearchResponse(items=response_items, next_cursor=next_cursor)


@router.get("/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(
    conversation_id: str,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
) -> ConversationHistory:
    """Return the full conversation history for a specific conversation."""

    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
        min_role=TenantRole.VIEWER,
    )
    actor = _conversation_actor(current_user, tenant_context)
    try:
        return await get_conversation_query_service().get_history(conversation_id, actor=actor)
    except ConversationNotFoundError as exc:  # pragma: no cover - mapped to HTTP below
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:  # pragma: no cover - turned into HTTP below
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/{conversation_id}/messages", response_model=PaginatedMessagesResponse)
async def get_conversation_messages(
    conversation_id: str,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None, description="Opaque pagination cursor."),
    direction: Literal["asc", "desc"] = Query(
        "desc",
        description="Sort order for messages; defaults to newest first.",
    ),
) -> PaginatedMessagesResponse:
    """Return a paginated slice of messages for a conversation."""

    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
        min_role=TenantRole.VIEWER,
    )
    actor = _conversation_actor(current_user, tenant_context)
    try:
        messages, next_cursor = await get_conversation_query_service().get_messages_page(
            conversation_id,
            actor=actor,
            limit=limit,
            cursor=cursor,
            direction=direction,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return PaginatedMessagesResponse(items=messages, next_cursor=next_cursor, prev_cursor=None)


@router.patch("/{conversation_id}/memory", response_model=ConversationMemoryConfigResponse)
async def update_conversation_memory(
    conversation_id: str,
    payload: ConversationMemoryConfigRequest,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:write")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
):
    """Set or clear memory strategy defaults for a conversation."""

    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
        min_role=TenantRole.ADMIN,
    )
    svc = get_conversation_service()
    payload_dict = payload.model_dump(exclude_unset=True)
    config = ConversationMemoryConfig(
        strategy=payload_dict.get("mode"),
        max_user_turns=payload_dict.get("max_user_turns"),
        keep_last_turns=payload_dict.get("keep_last_turns"),
        compact_trigger_turns=payload_dict.get("compact_trigger_turns"),
        compact_keep=payload_dict.get("compact_keep"),
        clear_tool_inputs=payload_dict.get("clear_tool_inputs"),
        memory_injection=payload_dict.get("memory_injection"),
    )
    try:
        await svc.set_memory_config(
            conversation_id,
            tenant_id=tenant_context.tenant_id,
            config=config,
            provided_fields=set(payload_dict.keys()),
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    persisted = await svc.get_memory_config(
        conversation_id,
        tenant_id=tenant_context.tenant_id,
    )
    if persisted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    raw_mode = persisted.strategy
    normalized_mode: Literal["none", "trim", "summarize", "compact"] | None = (
        cast(Literal["none", "trim", "summarize", "compact"], raw_mode)
        if raw_mode in {"none", "trim", "summarize", "compact"}
        else None
    )

    return ConversationMemoryConfigResponse(
        mode=normalized_mode,
        max_user_turns=persisted.max_user_turns,
        keep_last_turns=persisted.keep_last_turns,
        compact_trigger_turns=persisted.compact_trigger_turns,
        compact_keep=persisted.compact_keep,
        clear_tool_inputs=persisted.clear_tool_inputs,
        memory_injection=persisted.memory_injection,
    )


@router.patch("/{conversation_id}/title", response_model=ConversationTitleUpdateResponse)
async def update_conversation_title(
    conversation_id: str,
    payload: ConversationTitleUpdateRequest,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:write")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
) -> ConversationTitleUpdateResponse:
    """Rename a conversation title (manual override of auto-generated titles)."""

    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
        min_role=TenantRole.VIEWER,
    )

    try:
        normalized_title = await get_conversation_service().update_display_name(
            conversation_id,
            tenant_id=tenant_context.tenant_id,
            display_name=payload.display_name,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return ConversationTitleUpdateResponse(
        conversation_id=conversation_id,
        display_name=normalized_title,
    )


@router.get("/{conversation_id}/events", response_model=ConversationEventsResponse)
async def get_conversation_events(
    conversation_id: str,
    workflow_run_id: str | None = Query(
        None,
        description="Optional workflow run id to scope events to a single run.",
    ),
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
) -> ConversationEventsResponse:
    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
        min_role=TenantRole.VIEWER,
    )
    actor = _conversation_actor(current_user, tenant_context)
    try:
        events = await get_conversation_query_service().get_events(
            conversation_id,
            actor=actor,
            workflow_run_id=workflow_run_id,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    response_items: list[ConversationEventItem] = []
    for ev in events:
        response_items.append(
            ConversationEventItem(
                sequence_no=ev.sequence_no or 0,
                run_item_type=ev.run_item_type,
                run_item_name=ev.run_item_name,
                role=ev.role,
                agent=ev.agent,
                tool_call_id=ev.tool_call_id,
                tool_name=ev.tool_name,
                model=ev.model,
                content_text=ev.content_text,
                reasoning_text=ev.reasoning_text,
                call_arguments=ev.call_arguments,
                call_output=ev.call_output,
                attachments=[
                    MessageAttachment(
                        object_id=att.object_id,
                        filename=att.filename,
                        mime_type=att.mime_type,
                        size_bytes=att.size_bytes,
                        tool_call_id=att.tool_call_id,
                    )
                    for att in ev.attachments
                ],
                response_id=ev.response_id,
                workflow_run_id=getattr(ev, "workflow_run_id", None),
                timestamp=ev.timestamp.isoformat(),
            )
        )

    return ConversationEventsResponse(
        conversation_id=conversation_id,
        items=response_items,
    )


@router.get(
    "/{conversation_id}/stream",
    responses={200: TITLE_STREAM_RESPONSE},
)
async def stream_conversation_metadata(
    conversation_id: str,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
) -> StreamingResponse:
    """SSE stream of the conversation title generated from the first user message."""

    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
        min_role=TenantRole.VIEWER,
    )
    tenant_id = tenant_context.tenant_id

    record = await get_conversation_service().get_conversation(
        conversation_id,
        tenant_id=tenant_id,
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if record.display_name:

        async def _event_stream_existing_title() -> AsyncIterator[str]:
            yield f"data: {record.display_name}\n\n"
            yield "data: [DONE]\n\n"

        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }

        return StreamingResponse(
            _event_stream_existing_title(),
            media_type="text/event-stream",
            headers=headers,
        )

    first_user_message = next(
        (msg.content for msg in record.messages if msg.role == "user" and msg.content),
        "",
    ).strip()
    if not first_user_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation has no user messages"
        )

    async def _event_stream_generate_title() -> AsyncIterator[str]:
        emitted_any = False
        async for chunk in get_title_service().stream_title(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            first_user_message=first_user_message,
        ):
            if not chunk:
                continue
            emitted_any = True
            yield f"data: {chunk}\n\n"

        if not emitted_any:
            refreshed = await get_conversation_service().get_conversation(
                conversation_id,
                tenant_id=tenant_id,
            )
            if refreshed and refreshed.display_name:
                yield f"data: {refreshed.display_name}\n\n"

        yield "data: [DONE]\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
    }

    return StreamingResponse(
        _event_stream_generate_title(),
        media_type="text/event-stream",
        headers=headers,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:delete")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
) -> Response:
    """Remove all stored messages for the given conversation."""

    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
        min_role=TenantRole.ADMIN,
    )
    actor = _conversation_actor(current_user, tenant_context)
    await get_conversation_query_service().clear(conversation_id, actor=actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _resolve_tenant_context(
    current_user: CurrentUser,
    tenant_id_header: str | None,
    tenant_role_header: str | None,
    *,
    min_role: TenantRole,
) -> TenantContext:
    context = await get_tenant_context(
        tenant_id_header=tenant_id_header,
        tenant_role_header=tenant_role_header,
        current_user=current_user,
    )
    context.ensure_role(*_allowed_roles(min_role))
    return context


def _conversation_actor(
    current_user: CurrentUser, tenant_context: TenantContext
) -> ConversationActorContext:
    payload_obj = current_user.get("payload") if isinstance(current_user, dict) else None
    payload = payload_obj if isinstance(payload_obj, dict) else {}
    user_id = str(current_user.get("user_id") or payload.get("sub") or "anonymous")
    return ConversationActorContext(
        tenant_id=tenant_context.tenant_id,
        user_id=user_id,
    )


def _allowed_roles(min_role: TenantRole) -> tuple[TenantRole, ...]:
    if min_role is TenantRole.VIEWER:
        return (TenantRole.VIEWER, TenantRole.ADMIN, TenantRole.OWNER)
    if min_role is TenantRole.ADMIN:
        return (TenantRole.ADMIN, TenantRole.OWNER)
    return (TenantRole.OWNER,)
