"""Tenant team member management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.models.common import SuccessNoDataResponse
from app.api.models.team import (
    TeamMemberAddRequest,
    TeamMemberListResponse,
    TeamMemberResponse,
    TeamMemberRoleUpdateRequest,
)
from app.domain.team_errors import (
    InvalidTeamRoleError,
    OwnerRoleAssignmentError,
    TeamMemberAlreadyExistsError,
    TeamMemberNotFoundError,
)
from app.services.team.membership_service import (
    TenantMembershipService,
    get_tenant_membership_service,
)
from app.services.users.errors import LastOwnerRemovalError

router = APIRouter()


def _membership_service() -> TenantMembershipService:
    return get_tenant_membership_service()


@router.get("/members", response_model=TeamMemberListResponse)
async def list_members(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    context: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)),
    service: TenantMembershipService = Depends(_membership_service),
) -> TeamMemberListResponse:
    listing = await service.list_members(
        tenant_id=UUID(context.tenant_id),
        limit=limit,
        offset=offset,
    )
    members = [TeamMemberResponse.from_domain(member) for member in listing.members]
    return TeamMemberListResponse(members=members, total=listing.total)


@router.post(
    "/members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    payload: TeamMemberAddRequest,
    context: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)),
    service: TenantMembershipService = Depends(_membership_service),
) -> TeamMemberResponse:
    try:
        member = await service.add_member_by_email(
            tenant_id=UUID(context.tenant_id),
            email=str(payload.email),
            role=payload.role,
            actor_role=context.role,
        )
    except TeamMemberAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TeamMemberNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidTeamRoleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OwnerRoleAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return TeamMemberResponse.from_domain(member)


@router.patch("/members/{user_id}/role", response_model=TeamMemberResponse)
async def update_member_role(
    user_id: UUID,
    payload: TeamMemberRoleUpdateRequest,
    context: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)),
    service: TenantMembershipService = Depends(_membership_service),
) -> TeamMemberResponse:
    try:
        member = await service.update_role(
            tenant_id=UUID(context.tenant_id),
            user_id=user_id,
            role=payload.role,
            actor_role=context.role,
        )
    except TeamMemberNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidTeamRoleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LastOwnerRemovalError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except OwnerRoleAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return TeamMemberResponse.from_domain(member)


@router.delete("/members/{user_id}", response_model=SuccessNoDataResponse)
async def remove_member(
    user_id: UUID,
    context: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN, TenantRole.OWNER)),
    service: TenantMembershipService = Depends(_membership_service),
) -> SuccessNoDataResponse:
    try:
        await service.remove_member(
            tenant_id=UUID(context.tenant_id),
            user_id=user_id,
            actor_role=context.role,
        )
    except TeamMemberNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LastOwnerRemovalError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except OwnerRoleAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return SuccessNoDataResponse(message="Member removed successfully.")


__all__ = ["router"]
