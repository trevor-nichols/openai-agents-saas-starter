"""Current user profile endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies.auth import require_current_user
from app.api.v1.auth.utils import (
    extract_client_ip,
    extract_user_agent,
    hash_client_ip,
    hash_user_agent,
)
from app.api.v1.users.schemas import (
    CurrentUserProfileResponseData,
    CurrentUserProfileSuccessResponse,
    UserAccountDisableRequest,
    UserAccountDisableResponseData,
    UserAccountDisableSuccessResponse,
    UserEmailChangeRequest,
    UserEmailChangeResponseData,
    UserEmailChangeSuccessResponse,
    UserProfileUpdateRequest,
)
from app.domain.users import UserProfilePatch
from app.services.auth_service import auth_service
from app.services.security_events import get_security_event_service
from app.services.signup.email_verification_service import (
    EmailVerificationDeliveryError,
    get_email_verification_service,
)
from app.services.users import (
    EmailAlreadyInUseError,
    InvalidCredentialsError,
    LastOwnerRemovalError,
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


def _payload_dict(current_user: dict[str, Any]) -> dict[str, Any]:
    payload = current_user.get("payload")
    if isinstance(payload, dict):
        return payload
    return {}


def _require_user_id(current_user: dict[str, Any]) -> UUID:
    try:
        return UUID(current_user["user_id"])
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to resolve current user.",
        ) from exc


@router.get("/me", response_model=CurrentUserProfileSuccessResponse)
async def get_current_user_profile(
    current_user: dict[str, Any] = Depends(require_current_user),
) -> CurrentUserProfileSuccessResponse:
    """Return profile metadata for the current authenticated user."""

    payload = _payload_dict(current_user)
    user_id = _require_user_id(current_user)
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
            timezone=profile.timezone,
            locale=profile.locale,
            role=profile.role,
            email_verified=profile.email_verified,
        ),
    )


@router.patch("/me/profile", response_model=CurrentUserProfileSuccessResponse)
async def update_current_user_profile(
    payload: UserProfileUpdateRequest,
    current_user: dict[str, Any] = Depends(require_current_user),
) -> CurrentUserProfileSuccessResponse:
    """Update profile metadata for the current authenticated user."""

    user_id = _require_user_id(current_user)
    tenant_id = _require_tenant_id(_payload_dict(current_user))

    payload_dict = payload.model_dump(exclude_unset=True)
    if not payload_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one profile field must be provided.",
        )

    service = get_user_service()
    try:
        profile = await service.update_user_profile(
            user_id=user_id,
            tenant_id=tenant_id,
            update=UserProfilePatch(**payload_dict),
            provided_fields=set(payload_dict.keys()),
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except MembershipNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TenantContextRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return CurrentUserProfileSuccessResponse(
        message="User profile updated successfully",
        data=CurrentUserProfileResponseData(
            user_id=str(profile.user_id),
            tenant_id=str(profile.tenant_id),
            email=profile.email,
            display_name=profile.display_name,
            given_name=profile.given_name,
            family_name=profile.family_name,
            avatar_url=profile.avatar_url,
            timezone=profile.timezone,
            locale=profile.locale,
            role=profile.role,
            email_verified=profile.email_verified,
        ),
    )


@router.patch("/me/email", response_model=UserEmailChangeSuccessResponse)
async def change_current_user_email(
    payload: UserEmailChangeRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_current_user),
) -> UserEmailChangeSuccessResponse:
    """Change the current user's email and trigger verification."""

    user_id = _require_user_id(current_user)
    service = get_user_service()
    try:
        result = await service.change_email(
            user_id=user_id,
            current_password=payload.current_password,
            new_email=payload.new_email,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except EmailAlreadyInUseError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    verification_sent = False
    if result.changed:
        await auth_service.revoke_user_sessions(user_id, reason="email_change")
        email_service = get_email_verification_service()
        try:
            verification_sent = await email_service.send_verification_email(
                user_id=str(user_id),
                email=result.user.email,
                ip_address=extract_client_ip(request),
                user_agent=extract_user_agent(request),
            )
        except EmailVerificationDeliveryError:
            verification_sent = False

        await get_security_event_service().record(
            event_type="email_change",
            user_id=user_id,
            ip_hash=hash_client_ip(extract_client_ip(request)),
            user_agent_hash=hash_user_agent(extract_user_agent(request)),
            metadata={
                "email": result.user.email,
                "verification_sent": verification_sent,
            },
        )

    message = "Email updated successfully." if result.changed else "Email already up to date."
    return UserEmailChangeSuccessResponse(
        message=message,
        data=UserEmailChangeResponseData(
            user_id=str(user_id),
            email=result.user.email,
            email_verified=result.user.email_verified_at is not None,
            verification_sent=verification_sent,
        ),
    )


@router.post("/me/disable", response_model=UserAccountDisableSuccessResponse)
async def disable_current_user_account(
    payload: UserAccountDisableRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_current_user),
) -> UserAccountDisableSuccessResponse:
    """Disable the current user's account (soft delete)."""

    user_id = _require_user_id(current_user)
    service = get_user_service()
    try:
        await service.disable_account(
            user_id=user_id,
            current_password=payload.current_password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except LastOwnerRemovalError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    revoked = await auth_service.revoke_user_sessions(user_id, reason="account_disabled")
    await get_security_event_service().record(
        event_type="account_disabled",
        user_id=user_id,
        ip_hash=hash_client_ip(extract_client_ip(request)),
        user_agent_hash=hash_user_agent(extract_user_agent(request)),
    )

    return UserAccountDisableSuccessResponse(
        message="Account disabled successfully.",
        data=UserAccountDisableResponseData(
            user_id=str(user_id),
            disabled=True,
            revoked_sessions=revoked,
        ),
    )
