"""Current user profile endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import require_current_user
from app.api.v1.users.schemas import (
    CurrentUserProfileResponseData,
    CurrentUserProfileSuccessResponse,
)
from app.services.users import (
    InvalidCredentialsError,
    MembershipNotFoundError,
    TenantContextRequiredError,
    get_user_service,
)

router = APIRouter(prefix="/users", tags=["users"])


def _require_tenant_id(payload: dict[str, Any]) -> UUID:
    tenant_id = payload.get("tenant_id")
    if not isinstance(tenant_id, str) or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required for profile lookup.",
        )
    try:
        return UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context must be a valid UUID.",
        ) from exc


@router.get("/me", response_model=CurrentUserProfileSuccessResponse)
async def get_current_user_profile(
    current_user: dict[str, Any] = Depends(require_current_user),
) -> CurrentUserProfileSuccessResponse:
    """Return profile metadata for the current authenticated user."""

    payload = current_user.get("payload")
    if not isinstance(payload, dict):
        payload = {}

    try:
        user_id = UUID(current_user["user_id"])
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to resolve current user.",
        ) from exc

    tenant_id = _require_tenant_id(payload)

    service = get_user_service()
    try:
        profile = await service.get_user_profile_summary(user_id=user_id, tenant_id=tenant_id)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except MembershipNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TenantContextRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return CurrentUserProfileSuccessResponse(
        message="User profile retrieved successfully",
        data=CurrentUserProfileResponseData(
            user_id=str(profile.user_id),
            tenant_id=str(profile.tenant_id),
            email=profile.email,
            display_name=profile.display_name,
            given_name=profile.given_name,
            family_name=profile.family_name,
            avatar_url=profile.avatar_url,
            role=profile.role,
            email_verified=profile.email_verified,
        ),
    )
