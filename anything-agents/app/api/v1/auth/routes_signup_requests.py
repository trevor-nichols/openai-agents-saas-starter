"""Signup request submission and operator review endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import raise_rate_limit_http_error
from app.api.dependencies.auth import CurrentUser, require_scopes
from app.api.models.auth import (
    SignupAccessPolicyResponse,
    SignupInviteIssueResponse,
    SignupRequestApprovalRequest,
    SignupRequestDecisionResponse,
    SignupRequestListResponse,
    SignupRequestPublicRequest,
    SignupRequestRejectionRequest,
    SignupRequestResponse,
)
from app.api.v1.auth.utils import extract_client_ip, extract_user_agent
from app.core.config import get_settings
from app.domain.signup import SignupRequest, SignupRequestStatus
from app.services.rate_limit_service import RateLimitExceeded, RateLimitQuota, rate_limiter
from app.services.signup_request_service import (
    SignupRequestDecisionResult,
    SignupRequestNotFoundError,
    SignupRequestService,
    get_signup_request_service,
)

router = APIRouter(tags=["auth"])


def _request_service() -> SignupRequestService:
    return get_signup_request_service()


def _require_actor_id(user: CurrentUser) -> str:
    subject = user.get("sub") if isinstance(user, dict) else None
    if not isinstance(subject, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authenticated user missing subject claim.",
        )
    return subject


@router.post(
    "/request-access",
    response_model=SignupAccessPolicyResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_access_request(
    payload: SignupRequestPublicRequest,
    request: Request,
    service: SignupRequestService = Depends(_request_service),
) -> SignupAccessPolicyResponse:
    client_ip = extract_client_ip(request)
    await _enforce_public_quota(client_ip)
    await service.submit_request(
        email=payload.email,
        organization=payload.organization,
        full_name=payload.full_name,
        message=payload.message,
        ip_address=client_ip,
        user_agent=extract_user_agent(request),
        honeypot_value=payload.honeypot,
    )
    settings = get_settings()
    return SignupAccessPolicyResponse(
        policy=settings.signup_access_policy,
        invite_required=settings.signup_access_policy != "public",
        request_access_enabled=settings.signup_access_policy in {"invite_only", "approval"},
    )


@router.get(
    "/signup-requests",
    response_model=SignupRequestListResponse,
)
async def list_signup_requests(
    status_filter: SignupRequestStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _user: CurrentUser = Depends(require_scopes("auth:signup_requests")),
    service: SignupRequestService = Depends(_request_service),
) -> SignupRequestListResponse:
    listing = await service.list_requests(status=status_filter, limit=limit, offset=offset)
    return SignupRequestListResponse(
        requests=[_to_request_response(item) for item in listing.requests],
        total=listing.total,
    )


@router.post(
    "/signup-requests/{request_id}/approve",
    response_model=SignupRequestDecisionResponse,
)
async def approve_signup_request(
    request_id: UUID,
    payload: SignupRequestApprovalRequest,
    user: CurrentUser = Depends(require_scopes("auth:signup_requests")),
    service: SignupRequestService = Depends(_request_service),
) -> SignupRequestDecisionResponse:
    actor_user_id = _require_actor_id(user)
    try:
        result = await service.approve_request(
            request_id=request_id,
            actor_user_id=actor_user_id,
            note=payload.note,
            invite_expires_in_hours=payload.invite_expires_in_hours,
        )
    except SignupRequestNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    invite_response = _to_invite_issue_response(result)
    return SignupRequestDecisionResponse(
        request=_to_request_response(result.request),
        invite=invite_response,
    )


@router.post(
    "/signup-requests/{request_id}/reject",
    response_model=SignupRequestDecisionResponse,
)
async def reject_signup_request(
    request_id: UUID,
    payload: SignupRequestRejectionRequest,
    user: CurrentUser = Depends(require_scopes("auth:signup_requests")),
    service: SignupRequestService = Depends(_request_service),
) -> SignupRequestDecisionResponse:
    actor_user_id = _require_actor_id(user)
    try:
        result = await service.reject_request(
            request_id=request_id,
            actor_user_id=actor_user_id,
            reason=payload.reason,
        )
    except SignupRequestNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return SignupRequestDecisionResponse(
        request=_to_request_response(result.request),
        invite=None,
    )


async def _enforce_public_quota(client_ip: str | None) -> None:
    settings = get_settings()
    quota = RateLimitQuota(
        name="signup_request_per_hour",
        limit=settings.signup_rate_limit_per_hour,
        window_seconds=3600,
        scope="ip",
    )
    if quota.limit <= 0:
        return
    identity = client_ip or "unknown"
    try:
        await rate_limiter.enforce(quota, [identity])
    except RateLimitExceeded as exc:
        raise_rate_limit_http_error(exc, tenant_id="public-signup-request", user_id=identity)


def _to_request_response(record: SignupRequest) -> SignupRequestResponse:
    return SignupRequestResponse(
        id=record.id,
        email=record.email,
        organization=record.organization,
        full_name=record.full_name,
        status=record.status.value,
        created_at=record.created_at,
        decision_reason=record.decision_reason,
        invite_token_hint=record.signup_invite_token_hint,
    )


def _to_invite_issue_response(
    result: SignupRequestDecisionResult,
) -> SignupInviteIssueResponse | None:
    if result.invite is None:
        return None
    invite = result.invite.invite
    return SignupInviteIssueResponse(
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
        invite_token=result.invite.invite_token,
    )
