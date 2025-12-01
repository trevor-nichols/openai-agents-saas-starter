"""Public signup endpoint and helpers."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.api.models.auth import (
    SignupAccessPolicyResponse,
    UserRegisterRequest,
    UserRegisterResponse,
)
from app.api.v1.auth.rate_limit_helpers import apply_signup_quota
from app.api.v1.auth.utils import extract_client_ip, extract_user_agent, to_user_session_response
from app.core.settings import Settings, get_settings
from app.observability.metrics import record_signup_attempt
from app.services.billing.billing_service import (
    BillingError,
    InvalidTenantIdentifierError,
    PlanNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionStateError,
)
from app.services.shared.rate_limit_service import RateLimitQuota, build_rate_limit_identity
from app.services.signup.invite_service import (
    InviteExpiredError,
    InviteRequestMismatchError,
    InviteRevokedError,
    InviteTokenRequiredError,
)
from app.services.signup.signup_service import (
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
    settings = get_settings()
    policy = settings.signup_access_policy
    client_ip = extract_client_ip(request)
    user_agent = extract_user_agent(request)
    await _enforce_signup_quota(
        settings=settings,
        client_ip=client_ip,
        user_agent=user_agent,
        email=payload.email,
    )

    try:
        result = await signup_service.register(
            email=payload.email,
            password=payload.password,
            tenant_name=payload.tenant_name,
            display_name=payload.display_name,
            plan_code=payload.plan_code,
            trial_days=payload.trial_days,
            ip_address=client_ip,
            user_agent=user_agent,
            invite_token=payload.invite_token,
        )
    except PublicSignupDisabledError as exc:
        record_signup_attempt(result="register_error", policy=policy)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InviteTokenRequiredError as exc:
        record_signup_attempt(result="register_error", policy=policy)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InviteExpiredError as exc:
        record_signup_attempt(result="register_error", policy=policy)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InviteRevokedError as exc:
        record_signup_attempt(result="register_error", policy=policy)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InviteRequestMismatchError as exc:
        record_signup_attempt(result="register_error", policy=policy)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except EmailAlreadyRegisteredError as exc:
        record_signup_attempt(result="register_error", policy=policy)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TenantSlugCollisionError as exc:
        record_signup_attempt(result="register_error", policy=policy)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except BillingProvisioningError as exc:
        record_signup_attempt(result="register_error", policy=policy)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except BillingError as exc:
        record_signup_attempt(result="register_error", policy=policy)
        _handle_signup_billing_error(exc)

    session_payload = to_user_session_response(result.session)
    record_signup_attempt(result="register_success", policy=policy)
    return UserRegisterResponse(**session_payload.model_dump(), tenant_slug=result.tenant_slug)


async def _enforce_signup_quota(
    *,
    settings: Settings,
    client_ip: str | None,
    user_agent: str | None,
    email: str,
) -> None:
    policy = settings.signup_access_policy
    identity_parts = build_rate_limit_identity(
        client_ip,
        user_agent,
        include_user_agent=False,
    )
    ip_scope = client_ip or "unknown"
    await apply_signup_quota(
        RateLimitQuota(
            name="signup_per_hour",
            limit=settings.signup_rate_limit_per_hour,
            window_seconds=3600,
            scope="ip",
        ),
        key_parts=identity_parts,
        scope_value=ip_scope,
        policy=policy,
        flow="register",
    )
    await apply_signup_quota(
        RateLimitQuota(
            name="signup_per_day",
            limit=settings.signup_rate_limit_per_day,
            window_seconds=86400,
            scope="ip",
        ),
        key_parts=identity_parts,
        scope_value=ip_scope,
        policy=policy,
        flow="register",
    )

    normalized_email = email.strip().lower()
    if settings.signup_rate_limit_per_email_day > 0:
        await apply_signup_quota(
            RateLimitQuota(
                name="signup_per_email_day",
                limit=settings.signup_rate_limit_per_email_day,
                window_seconds=86400,
                scope="email",
            ),
            key_parts=[normalized_email],
            scope_value=normalized_email,
            policy=policy,
            flow="register",
        )

    domain = normalized_email.split("@")[-1] if "@" in normalized_email else None
    if domain and settings.signup_rate_limit_per_domain_day > 0:
        await apply_signup_quota(
            RateLimitQuota(
                name="signup_per_domain_day",
                limit=settings.signup_rate_limit_per_domain_day,
                window_seconds=86400,
                scope="domain",
            ),
            key_parts=[domain],
            scope_value=domain,
            policy=policy,
            flow="register",
        )


def _handle_signup_billing_error(exc: BillingError) -> None:
    if isinstance(exc, PlanNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, SubscriptionStateError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, (InvalidTenantIdentifierError, SubscriptionNotFoundError)):  # noqa: UP038
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
