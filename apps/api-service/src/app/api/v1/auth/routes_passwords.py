"""Password reset/change endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import raise_rate_limit_http_error
from app.api.dependencies.auth import require_current_user, require_verified_scopes
from app.api.models.auth import (
    PasswordChangeRequest,
    PasswordForgotRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
)
from app.api.models.common import SuccessResponse
from app.api.v1.auth.utils import (
    extract_client_ip,
    extract_user_agent,
    hash_client_ip,
    hash_user_agent,
)
from app.services.auth_service import auth_service
from app.services.security_events import get_security_event_service
from app.services.shared.rate_limit_service import RateLimitExceeded, RateLimitQuota, rate_limiter
from app.services.signup.password_recovery_service import (
    InvalidPasswordResetTokenError,
    PasswordResetDeliveryError,
    get_password_recovery_service,
)
from app.services.users import (
    InvalidCredentialsError,
    MembershipNotFoundError,
    PasswordPolicyViolationError,
    PasswordReuseError,
    get_user_service,
)

router = APIRouter(tags=["auth"])


@router.post(
    "/password/forgot",
    response_model=SuccessResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_password_reset(
    payload: PasswordForgotRequest,
    request: Request,
) -> SuccessResponse:
    client_ip = extract_client_ip(request)
    await _enforce_password_reset_quota(email=payload.email, client_ip=client_ip)
    service = get_password_recovery_service()
    try:
        await service.request_password_reset(
            email=payload.email,
            ip_address=client_ip,
            user_agent=extract_user_agent(request),
        )
    except PasswordResetDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to send password reset email. Please try again shortly.",
        ) from exc
    return SuccessResponse(
        message="If the account exists, password reset instructions have been sent.",
        data=None,
    )


@router.post("/password/confirm", response_model=SuccessResponse)
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    request: Request,
) -> SuccessResponse:
    try:
        service = get_password_recovery_service()
        await service.confirm_password_reset(
            token=payload.token,
            new_password=payload.new_password,
            ip_address=extract_client_ip(request),
            user_agent=extract_user_agent(request),
        )
    except InvalidPasswordResetTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PasswordPolicyViolationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PasswordReuseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await get_security_event_service().record(
        event_type="password_reset_token",
        user_id=None,
        ip_hash=hash_client_ip(extract_client_ip(request)),
        user_agent_hash=hash_user_agent(extract_user_agent(request)),
    )
    return SuccessResponse(message="Password has been reset successfully.", data=None)


@router.post("/password/change", response_model=SuccessResponse)
async def change_password(
    payload: PasswordChangeRequest,
    request: Request,
    current_user: dict[str, str] = Depends(require_current_user),
) -> SuccessResponse:
    service = get_user_service()
    user_uuid = UUID(current_user["user_id"])
    try:
        await service.change_password(
            user_id=user_uuid,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except PasswordPolicyViolationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PasswordReuseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await auth_service.revoke_user_sessions(user_uuid, reason="password_change")
    await get_security_event_service().record(
        event_type="password_change",
        user_id=user_uuid,
        ip_hash=hash_client_ip(extract_client_ip(request)),
        user_agent_hash=hash_user_agent(extract_user_agent(request)),
    )
    return SuccessResponse(message="Password updated successfully", data=None)


@router.post("/password/reset", response_model=SuccessResponse)
async def admin_reset_password(
    payload: PasswordResetRequest,
    request: Request,
    current_user: dict[str, object] = Depends(require_verified_scopes("support:read")),
) -> SuccessResponse:
    tenant_claim: object | None = None
    payload_claim = current_user.get("payload")
    if isinstance(payload_claim, dict):
        tenant_claim = payload_claim.get("tenant_id")
    if not tenant_claim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context is required for password reset.",
        )
    try:
        tenant_id = UUID(str(tenant_claim))
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant id.",
        ) from exc

    service = get_user_service()
    try:
        await service.admin_reset_password(
            target_user_id=payload.user_id,
            tenant_id=tenant_id,
            new_password=payload.new_password,
        )
    except MembershipNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PasswordPolicyViolationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PasswordReuseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await auth_service.revoke_user_sessions(payload.user_id, reason="password_reset")
    await get_security_event_service().record(
        event_type="password_reset_admin",
        user_id=payload.user_id,
        tenant_id=tenant_id,
        ip_hash=hash_client_ip(extract_client_ip(request)),
        user_agent_hash=hash_user_agent(extract_user_agent(request)),
    )
    return SuccessResponse(message="Password reset successfully", data=None)


async def _enforce_password_reset_quota(email: str, client_ip: str | None) -> None:
    from app.core.settings import get_settings

    settings = get_settings()
    quotas: list[tuple[RateLimitQuota, list[str]]] = []
    per_email = settings.password_reset_email_rate_limit_per_hour
    if per_email > 0:
        quotas.append(
            (
                RateLimitQuota(
                    name="password_reset_email",
                    limit=per_email,
                    window_seconds=3600,
                    scope="email",
                ),
                [email.strip().lower()],
            )
        )
    per_ip = settings.password_reset_ip_rate_limit_per_hour
    if per_ip > 0 and client_ip:
        quotas.append(
            (
                RateLimitQuota(
                    name="password_reset_ip",
                    limit=per_ip,
                    window_seconds=3600,
                    scope="ip",
                ),
                [client_ip],
            )
        )
    for quota, keys in quotas:
        try:
            await rate_limiter.enforce(quota, keys)
        except RateLimitExceeded as exc:
            raise_rate_limit_http_error(exc, tenant_id="password-reset", user_id=keys[0])
