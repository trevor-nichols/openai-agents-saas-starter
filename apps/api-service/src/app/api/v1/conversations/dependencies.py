"""Shared helpers for conversation-scoped routers."""

from __future__ import annotations

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.tenant import TenantContext, TenantRole, get_tenant_context
from app.services.agents.context import ConversationActorContext


def allowed_roles(min_role: TenantRole) -> tuple[TenantRole, ...]:
    if min_role is TenantRole.VIEWER:
        return (TenantRole.VIEWER, TenantRole.MEMBER, TenantRole.ADMIN, TenantRole.OWNER)
    if min_role is TenantRole.ADMIN:
        return (TenantRole.ADMIN, TenantRole.OWNER)
    return (TenantRole.OWNER,)


async def resolve_tenant_context(
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
    context.ensure_role(*allowed_roles(min_role))
    return context


def conversation_actor(
    current_user: CurrentUser,
    tenant_context: TenantContext,
) -> ConversationActorContext:
    payload_obj = current_user.get("payload") if isinstance(current_user, dict) else None
    payload = payload_obj if isinstance(payload_obj, dict) else {}
    user_id = str(current_user.get("user_id") or payload.get("sub") or "anonymous")
    return ConversationActorContext(
        tenant_id=tenant_context.tenant_id,
        user_id=user_id,
    )


__all__ = ["TenantRole", "conversation_actor", "resolve_tenant_context"]
