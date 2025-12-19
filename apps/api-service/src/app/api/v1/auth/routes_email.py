"""Email verification endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import raise_rate_limit_http_error
from app.api.dependencies.auth import require_current_user
from app.api.models.auth import (
    EmailVerificationConfirmRequest,
    EmailVerificationSendSuccessResponse,
    EmailVerificationStatusResponseData,
)
from app.api.models.common import SuccessNoDataResponse
from app.api.v1.auth.utils import extract_client_ip, extract_user_agent
from app.services.shared.rate_limit_service import RateLimitExceeded, RateLimitQuota, rate_limiter
from app.services.signup.email_verification_service import (
    EmailVerificationDeliveryError,
    InvalidEmailVerificationTokenError,
    get_email_verification_service,
)

router = APIRouter(tags=["auth"])


@router.post(
    "/email/send",
    response_model=EmailVerificationSendSuccessResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_email_verification(
    request: Request,
    current_user: dict[str, Any] = Depends(require_current_user),
) -> EmailVerificationSendSuccessResponse:
    payload = current_user.get("payload", {})
    if bool(payload.get("email_verified")):
        return EmailVerificationSendSuccessResponse(
            message="Email already verified.",
            data=EmailVerificationStatusResponseData(email_verified=True),
        )

    client_ip = extract_client_ip(request)
    await _enforce_email_verification_quota(current_user["user_id"], client_ip)

    service = get_email_verification_service()
    try:
        await service.send_verification_email(
            user_id=current_user["user_id"],
            email=None,
            ip_address=client_ip,
            user_agent=extract_user_agent(request),
        )
    except EmailVerificationDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to send verification email. Please try again shortly.",
        ) from exc

    return EmailVerificationSendSuccessResponse(
        message="Verification email sent.",
        data=EmailVerificationStatusResponseData(email_verified=False),
    )


@router.post("/email/verify", response_model=SuccessNoDataResponse)
async def verify_email_token(
    payload: EmailVerificationConfirmRequest,
    request: Request,
) -> SuccessNoDataResponse:
    service = get_email_verification_service()
    try:
        await service.verify_token(
            token=payload.token,
            ip_address=extract_client_ip(request),
            user_agent=extract_user_agent(request),
        )
    except InvalidEmailVerificationTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return SuccessNoDataResponse(message="Email verified successfully.")


async def _enforce_email_verification_quota(user_id: str, client_ip: str | None) -> None:
    from app.core.settings import get_settings

    settings = get_settings()
    quotas: list[tuple[RateLimitQuota, list[str]]] = []
    per_user = settings.email_verification_email_rate_limit_per_hour
    if per_user > 0:
        quotas.append(
            (
                RateLimitQuota(
                    name="email_verify_user",
                    limit=per_user,
                    window_seconds=3600,
                    scope="user",
                ),
                [user_id],
            )
        )
    per_ip = settings.email_verification_ip_rate_limit_per_hour
    if per_ip > 0 and client_ip:
        quotas.append(
            (
                RateLimitQuota(
                    name="email_verify_ip",
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
            raise_rate_limit_http_error(exc, tenant_id="email-verification", user_id=keys[0])
