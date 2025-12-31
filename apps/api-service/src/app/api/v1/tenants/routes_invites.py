"""Tenant invite management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies.auth import require_current_user
from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.models.auth import UserSessionResponse
from app.api.models.team import (
    TeamInviteAcceptExistingRequest,
    TeamInviteAcceptRequest,
    TeamInviteIssueRequest,
    TeamInviteIssueResponse,
    TeamInviteListResponse,
    TeamInvitePolicyResponse,
    TeamInviteResponse,
)
from app.api.v1.auth.utils import extract_client_ip, extract_user_agent, to_user_session_response
from app.domain.team import TeamInviteStatus
from app.domain.team_errors import (
    InvalidTeamRoleError,
    OwnerRoleAssignmentError,
    TeamInviteDeliveryError,
    TeamInviteEmailMismatchError,
    TeamInviteExpiredError,
    TeamInviteNotFoundError,
    TeamInviteRevokedError,
    TeamInviteUserExistsError,
    TeamInviteValidationError,
    TeamMemberAlreadyExistsError,
)
from app.domain.team_policy import TEAM_INVITE_POLICY
from app.services.auth_service import UserAuthenticationError, auth_service
from app.services.team.invite_service import TeamInviteService, get_team_invite_service

router = APIRouter()

_ADMIN_ROLES: tuple[TenantRole, ...] = (TenantRole.ADMIN, TenantRole.OWNER)
_VIEWER_ROLES: tuple[TenantRole, ...] = (
    TenantRole.VIEWER,
    TenantRole.MEMBER,
    TenantRole.ADMIN,
    TenantRole.OWNER,
)


def _invite_service() -> TeamInviteService:
    return get_team_invite_service()


@router.get("/invites/policy", response_model=TeamInvitePolicyResponse)
async def get_invite_policy(
    _: TenantContext = Depends(require_tenant_role(*_VIEWER_ROLES)),
) -> TeamInvitePolicyResponse:
    return TeamInvitePolicyResponse(
        default_expires_hours=TEAM_INVITE_POLICY.default_expires_hours,
        max_expires_hours=TEAM_INVITE_POLICY.max_expires_hours,
    )


@router.get("/invites", response_model=TeamInviteListResponse)
async def list_invites(
    status_filter: TeamInviteStatus | None = Query(default=None, alias="status"),
    invited_email: str | None = Query(default=None, alias="email"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    context: TenantContext = Depends(require_tenant_role(*_ADMIN_ROLES)),
    service: TeamInviteService = Depends(_invite_service),
) -> TeamInviteListResponse:
    try:
        listing = await service.list_invites(
            tenant_id=UUID(context.tenant_id),
            status=status_filter,
            email=invited_email,
            limit=limit,
            offset=offset,
        )
    except TeamInviteValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    invites = [TeamInviteResponse.from_domain(invite) for invite in listing.invites]
    return TeamInviteListResponse(invites=invites, total=listing.total)


@router.post(
    "/invites",
    response_model=TeamInviteIssueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def issue_invite(
    payload: TeamInviteIssueRequest,
    context: TenantContext = Depends(require_tenant_role(*_ADMIN_ROLES)),
    service: TeamInviteService = Depends(_invite_service),
) -> TeamInviteIssueResponse:
    user_id_value = context.user.get("user_id") if isinstance(context.user, dict) else None
    created_by = None
    if isinstance(user_id_value, str):
        try:
            created_by = UUID(user_id_value)
        except ValueError:
            created_by = None
    try:
        result = await service.issue_invite(
            tenant_id=UUID(context.tenant_id),
            invited_email=str(payload.invited_email),
            role=payload.role,
            created_by_user_id=created_by,
            actor_role=context.role,
            expires_in_hours=payload.expires_in_hours,
        )
    except TeamMemberAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidTeamRoleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OwnerRoleAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TeamInviteValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TeamInviteDeliveryError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    invite_response = TeamInviteResponse.from_domain(result.invite)
    return TeamInviteIssueResponse(
        **invite_response.model_dump(),
        invite_token=result.invite_token,
    )


@router.post("/invites/{invite_id}/revoke", response_model=TeamInviteResponse)
async def revoke_invite(
    invite_id: UUID,
    context: TenantContext = Depends(require_tenant_role(*_ADMIN_ROLES)),
    service: TeamInviteService = Depends(_invite_service),
) -> TeamInviteResponse:
    user_id_value = context.user.get("user_id") if isinstance(context.user, dict) else None
    actor_user_id: UUID | None = None
    if isinstance(user_id_value, str):
        try:
            actor_user_id = UUID(user_id_value)
        except ValueError:
            actor_user_id = None
    try:
        record = await service.revoke_invite(
            invite_id,
            tenant_id=UUID(context.tenant_id),
            actor_user_id=actor_user_id,
            reason="tenant_admin_action",
        )
    except TeamInviteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TeamInviteRevokedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TeamInviteResponse.from_domain(record)


@router.post(
    "/invites/accept",
    response_model=UserSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def accept_invite(
    payload: TeamInviteAcceptRequest,
    request: Request,
    service: TeamInviteService = Depends(_invite_service),
) -> UserSessionResponse:
    try:
        result = await service.accept_invite_for_new_user(
            token=payload.token,
            password=payload.password,
            display_name=payload.display_name,
        )
    except TeamInviteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TeamInviteExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    except TeamInviteRevokedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TeamInviteValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TeamInviteUserExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    try:
        tokens = await auth_service.login_user(
            email=result.email,
            password=payload.password,
            tenant_id=str(result.tenant_id),
            ip_address=extract_client_ip(request),
            user_agent=extract_user_agent(request),
        )
    except UserAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return to_user_session_response(tokens)


@router.post("/invites/accept/current", response_model=TeamInviteResponse)
async def accept_invite_existing_user(
    payload: TeamInviteAcceptExistingRequest,
    current_user: dict[str, object] = Depends(require_current_user),
    service: TeamInviteService = Depends(_invite_service),
) -> TeamInviteResponse:
    user_id = UUID(str(current_user["user_id"]))
    try:
        invite = await service.accept_invite_for_existing_user(
            token=payload.token,
            user_id=user_id,
        )
    except TeamInviteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TeamInviteExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    except TeamInviteRevokedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TeamInviteEmailMismatchError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TeamMemberAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TeamInviteResponse.from_domain(invite)


__all__ = ["router"]
