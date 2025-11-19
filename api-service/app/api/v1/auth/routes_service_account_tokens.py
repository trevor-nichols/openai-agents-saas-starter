"""Authenticated management endpoints for service-account refresh tokens."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status

from app.api.dependencies.service_accounts import (
    ServiceAccountActor,
    ServiceAccountActorType,
    require_service_account_actor,
)
from app.api.models.auth import (
    ServiceAccountTokenItem,
    ServiceAccountTokenListResponse,
    ServiceAccountTokenRevokeRequest,
)
from app.api.models.common import SuccessResponse
from app.domain.auth import ServiceAccountTokenStatus
from app.services.auth_service import auth_service

router = APIRouter(tags=["auth"])


@router.get(
    "/service-accounts/tokens",
    response_model=ServiceAccountTokenListResponse,
)
async def list_service_account_tokens(
    account: str | None = Query(
        default=None,
        description="Filter by service-account identifier (substring match).",
    ),
    fingerprint: str | None = Query(
        default=None,
        description="Filter by stored fingerprint.",
    ),
    status_filter: ServiceAccountTokenStatus = Query(
        default=ServiceAccountTokenStatus.ACTIVE,
        alias="status",
        description="Token status filter (active, revoked, all).",
    ),
    tenant_id: str | None = Query(
        default=None,
        description="Tenant UUID to filter (operator override only).",
    ),
    include_global: bool = Query(
        default=False,
        description="Include tenantless tokens (operator override only).",
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Max tokens to return."),
    offset: int = Query(default=0, ge=0, description="Offset for pagination."),
    actor: ServiceAccountActor = Depends(require_service_account_actor),
) -> ServiceAccountTokenListResponse:
    tenant_ids, include_global_flag = _resolve_scope(actor, tenant_id, include_global)
    result = await auth_service.list_service_account_tokens(
        tenant_ids=tenant_ids,
        include_global=include_global_flag,
        account_query=account,
        fingerprint=fingerprint,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    items = [
        ServiceAccountTokenItem(
            jti=token.jti,
            account=token.account,
            tenant_id=token.tenant_id,
            scopes=token.scopes,
            issued_at=token.issued_at,
            expires_at=token.expires_at,
            revoked_at=token.revoked_at,
            revoked_reason=token.revoked_reason,
            fingerprint=token.fingerprint,
            signing_kid=token.signing_kid,
        )
        for token in result.tokens
    ]
    return ServiceAccountTokenListResponse(
        items=items,
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/service-accounts/tokens/{jti}/revoke",
    response_model=SuccessResponse,
)
async def revoke_service_account_token(
    jti: str = Path(..., description="Refresh token identifier (JWT jti)."),
    payload: ServiceAccountTokenRevokeRequest = Body(...),
    actor: ServiceAccountActor = Depends(require_service_account_actor),
) -> SuccessResponse:
    reason = payload.reason or actor.reason
    if actor.actor_type == ServiceAccountActorType.PLATFORM_OPERATOR and not reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reason is required when using operator override.",
        )
    if not reason:
        reason = "tenant_admin_manual_revoke"

    await auth_service.revoke_service_account_token(jti, reason=reason)
    return SuccessResponse(message="Service account token revoked.", data={"jti": jti})


def _resolve_scope(
    actor: ServiceAccountActor,
    tenant_id_param: str | None,
    include_global_param: bool,
) -> tuple[list[str] | None, bool]:
    if actor.actor_type == ServiceAccountActorType.TENANT_ADMIN:
        if tenant_id_param and tenant_id_param != actor.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant administrators may only query their own tenant.",
            )
        tenant_ids = [actor.tenant_id] if actor.tenant_id else None
        return tenant_ids, False

    tenant_ids = [tenant_id_param] if tenant_id_param else None
    return tenant_ids, include_global_param
