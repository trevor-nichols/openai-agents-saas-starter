"""Operator endpoints for issuing and revoking signup invites."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import CurrentUser, require_scopes
from app.api.models.auth import (
    SignupInviteIssueRequest,
    SignupInviteIssueResponse,
    SignupInviteListResponse,
    SignupInviteResponse,
)
from app.domain.signup import SignupInvite, SignupInviteStatus
from app.services.signup.invite_service import (
    InviteNotFoundError,
    InviteService,
    get_invite_service,
)

router = APIRouter(tags=["auth"])


def _invite_service() -> InviteService:
    return get_invite_service()


@router.get("/invites", response_model=SignupInviteListResponse)
async def list_invites(
    status_filter: SignupInviteStatus | None = Query(default=None, alias="status"),
    invited_email: str | None = Query(default=None, alias="email"),
    request_id: UUID | None = Query(default=None, alias="request_id"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _user: CurrentUser = Depends(require_scopes("auth:invites")),
    service: InviteService = Depends(_invite_service),
) -> SignupInviteListResponse:
    listing = await service.list_invites(
        status=status_filter,
        email=invited_email,
        signup_request_id=request_id,
        limit=limit,
        offset=offset,
    )
    invites = [_to_invite_response(item) for item in listing.invites]
    return SignupInviteListResponse(invites=invites, total=listing.total)


@router.post(
    "/invites",
    response_model=SignupInviteIssueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def issue_invite(
    payload: SignupInviteIssueRequest,
    user: CurrentUser = Depends(require_scopes("auth:invites")),
    service: InviteService = Depends(_invite_service),
) -> SignupInviteIssueResponse:
    result = await service.issue_invite(
        issuer_user_id=user.get("sub"),
        issuer_tenant_id=None,
        invited_email=payload.invited_email,
        max_redemptions=payload.max_redemptions,
        expires_in_hours=payload.expires_in_hours,
        note=payload.note,
        signup_request_id=payload.signup_request_id,
    )
    invite_response = _to_invite_response(result.invite)
    return SignupInviteIssueResponse(
        **invite_response.model_dump(),
        invite_token=result.invite_token,
    )


@router.post(
    "/invites/{invite_id}/revoke",
    response_model=SignupInviteResponse,
)
async def revoke_invite(
    invite_id: UUID,
    _user: CurrentUser = Depends(require_scopes("auth:invites")),
    service: InviteService = Depends(_invite_service),
) -> SignupInviteResponse:
    try:
        record = await service.revoke_invite(invite_id, reason="operator_action")
    except InviteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_invite_response(record)


def _to_invite_response(invite: SignupInvite) -> SignupInviteResponse:
    return SignupInviteResponse(
        id=invite.id,
        token_hint=invite.token_hint,
        invited_email=invite.invited_email,
        status=invite.status.value,
        max_redemptions=invite.max_redemptions,
        redeemed_count=invite.redeemed_count,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
        signup_request_id=invite.signup_request_id,
        note=invite.note,
    )
