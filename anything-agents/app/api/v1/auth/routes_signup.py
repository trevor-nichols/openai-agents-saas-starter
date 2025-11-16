"""Public signup endpoint and helpers."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.api.dependencies import raise_rate_limit_http_error
from app.api.models.auth import (
    SignupAccessPolicyResponse,
    UserRegisterRequest,
    UserRegisterResponse,
)
from app.api.v1.auth.utils import extract_client_ip, extract_user_agent, to_user_session_response
from app.core.config import get_settings
from app.services.billing_service import (
    BillingError,
    InvalidTenantIdentifierError,
    PlanNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionStateError,
)
from app.services.invite_service import (
    InviteExpiredError,
    InviteRequestMismatchError,
    InviteRevokedError,
    InviteTokenRequiredError,
)
from app.services.rate_limit_service import RateLimitExceeded, RateLimitQuota, rate_limiter
from app.services.signup_service import (
    BillingProvisioningError,
    EmailAlreadyRegisteredError,
    PublicSignupDisabledError,
    TenantSlugCollisionError,
    signup_service,
)

router = APIRouter(tags=["auth"])


@router.get("/signup-policy", response_model=SignupAccessPolicyResponse)
async def get_signup_access_policy() -> SignupAccessPolicyResponse:
    settings = get_settings()
    policy = settings.signup_access_policy
    return SignupAccessPolicyResponse(
        policy=policy,
        invite_required=policy != "public",
        request_access_enabled=policy in {"invite_only", "approval"},
    )


@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_tenant(
    payload: UserRegisterRequest,
    request: Request,
) -> UserRegisterResponse:
    client_ip = extract_client_ip(request)
    await _enforce_signup_quota(client_ip)

    try:
        result = await signup_service.register(
            email=payload.email,
            password=payload.password,
            tenant_name=payload.tenant_name,
            display_name=payload.display_name,
            plan_code=payload.plan_code,
            trial_days=payload.trial_days,
            ip_address=client_ip,
            user_agent=extract_user_agent(request),
            invite_token=payload.invite_token,
        )
    except PublicSignupDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InviteTokenRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InviteExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InviteRevokedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InviteRequestMismatchError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TenantSlugCollisionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except BillingProvisioningError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except BillingError as exc:
        _handle_signup_billing_error(exc)

    session_payload = to_user_session_response(result.session)
    return UserRegisterResponse(**session_payload.model_dump(), tenant_slug=result.tenant_slug)


async def _enforce_signup_quota(client_ip: str | None) -> None:
    settings = get_settings()
    quota = RateLimitQuota(
        name="signup_per_hour",
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
        raise_rate_limit_http_error(exc, tenant_id="public-signup", user_id=identity)


def _handle_signup_billing_error(exc: BillingError) -> None:
    if isinstance(exc, PlanNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, SubscriptionStateError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, (InvalidTenantIdentifierError, SubscriptionNotFoundError)):  # noqa: UP038
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
