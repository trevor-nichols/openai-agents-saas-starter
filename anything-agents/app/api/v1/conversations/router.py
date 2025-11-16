"""Conversation management endpoints."""

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.dependencies.tenant import TenantContext, TenantRole, get_tenant_context
from app.api.v1.conversations.schemas import ConversationHistory, ConversationSummary
from app.services.agent_service import ConversationActorContext, agent_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
) -> list[ConversationSummary]:
    """List stored conversations ordered by recency."""

    tenant_context = await _resolve_tenant_context(
        current_user,
        tenant_id_header,
        tenant_role_header,
        min_role=TenantRole.VIEWER,
    )
    actor = _conversation_actor(current_user, tenant_context)
    return await agent_service.list_conversations(actor=actor)


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
        return await agent_service.get_conversation_history(conversation_id, actor=actor)
    except ValueError as exc:  # pragma: no cover - turned into HTTP below
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


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
    await agent_service.clear_conversation(conversation_id, actor=actor)
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
