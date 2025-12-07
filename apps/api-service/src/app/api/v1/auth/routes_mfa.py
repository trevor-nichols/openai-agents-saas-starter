"""MFA enrollment and management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies.auth import require_current_user
from app.api.models.auth import UserSessionResponse
from app.api.models.common import SuccessResponse
from app.api.models.mfa import (
    MfaChallengeCompleteRequest,
    MfaMethodView,
    RecoveryCodesResponse,
    TotpEnrollResponse,
    TotpVerifyRequest,
)
from app.api.v1.auth.utils import (
    extract_client_ip,
    extract_user_agent,
    hash_client_ip,
    hash_user_agent,
    to_user_session_response,
)
from app.core.security import get_token_verifier
from app.core.settings import get_settings
from app.services.auth.mfa_service import (
    MfaService,
    MfaVerificationError,
    get_mfa_service,
)
from app.services.auth_service import UserAuthenticationError, auth_service
from app.services.shared.rate_limit_service import (
    RateLimitExceeded,
    RateLimitQuota,
    rate_limiter,
)

router = APIRouter(tags=["auth"])


def _service() -> MfaService:
    return get_mfa_service()


@router.get("/mfa", response_model=list[MfaMethodView])
async def list_mfa_methods(
    current_user: dict[str, str] = Depends(require_current_user),
) -> list[MfaMethodView]:
    service = _service()
    methods = await service.list_methods(UUID(current_user["user_id"]))
    return [
        MfaMethodView(
            id=item.id,
            method_type=item.method_type.value,
            label=item.label,
            verified_at=item.verified_at.isoformat() if item.verified_at else None,
            last_used_at=item.last_used_at.isoformat() if item.last_used_at else None,
            revoked_at=item.revoked_at.isoformat() if item.revoked_at else None,
        )
        for item in methods
    ]


@router.post("/mfa/totp/enroll", response_model=TotpEnrollResponse, status_code=201)
async def start_totp_enrollment(
    label: str | None = None,
    current_user: dict[str, str] = Depends(require_current_user),
) -> TotpEnrollResponse:
    service = _service()
    secret, method_id = await service.start_totp_enrollment(
        user_id=UUID(current_user["user_id"]),
        label=label,
    )
    otpauth_url = None
    try:
        otpauth_url = f"otpauth://totp/OpenAI-Agent:{current_user.get('email','user')}?secret={secret}&issuer=OpenAI-Agent"
    except Exception:
        otpauth_url = None
    return TotpEnrollResponse(secret=secret, method_id=method_id, otpauth_url=otpauth_url)


@router.post("/mfa/totp/verify", response_model=SuccessResponse)
async def verify_totp(
    payload: TotpVerifyRequest,
    request: Request,
    current_user: dict[str, str] = Depends(require_current_user),
) -> SuccessResponse:
    service = _service()
    client_ip = extract_client_ip(request)
    await _enforce_mfa_verify_quota(current_user["user_id"], client_ip)
    try:
        await service.verify_totp(
            user_id=UUID(current_user["user_id"]),
            method_id=payload.method_id,
            code=payload.code,
            ip_hash=hash_client_ip(client_ip),
            user_agent_hash=hash_user_agent(extract_user_agent(request)),
        )
    except MfaVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SuccessResponse(message="MFA verified.", data=None)


@router.delete("/mfa/{method_id}", response_model=SuccessResponse)
async def revoke_mfa_method(
    method_id: UUID,
    current_user: dict[str, str] = Depends(require_current_user),
) -> SuccessResponse:
    service = _service()
    await service.revoke_method(
        user_id=UUID(current_user["user_id"]), method_id=method_id, reason="user_request"
    )
    return SuccessResponse(message="MFA method revoked.", data=None)


@router.post("/mfa/recovery/regenerate", response_model=RecoveryCodesResponse)
async def regenerate_recovery_codes(
    current_user: dict[str, str] = Depends(require_current_user),
) -> RecoveryCodesResponse:
    service = _service()
    codes = await service.regenerate_recovery_codes(user_id=UUID(current_user["user_id"]))
    return RecoveryCodesResponse(codes=codes)


@router.post("/mfa/complete", response_model=UserSessionResponse)
async def complete_mfa_challenge(
    payload: MfaChallengeCompleteRequest,
    request: Request,
) -> UserSessionResponse:
    client_ip = extract_client_ip(request)
    user_id = _extract_challenge_user_id(payload.challenge_token)
    await _enforce_mfa_verify_quota(user_id, client_ip)
    user_agent = extract_user_agent(request)
    try:
        tokens = await auth_service.complete_mfa_challenge(
            challenge_token=payload.challenge_token,
            method_id=payload.method_id,
            code=payload.code,
            ip_address=client_ip,
            user_agent=user_agent,
            ip_hash=hash_client_ip(client_ip),
            user_agent_hash=hash_user_agent(user_agent),
        )
    except (MfaVerificationError, UserAuthenticationError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return to_user_session_response(tokens)


def _extract_challenge_user_id(challenge_token: str) -> UUID:
    verifier = get_token_verifier(get_settings())
    try:
        payload = verifier.verify(challenge_token)
    except Exception as exc:  # pragma: no cover - defensive
        raise UserAuthenticationError("MFA challenge token verification failed.") from exc

    if payload.get("token_use") != "mfa_challenge":
        raise UserAuthenticationError("Invalid MFA challenge token.")
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.startswith("user:"):
        raise UserAuthenticationError("Challenge token subject is malformed.")
    try:
        return UUID(sub.split(":", 1)[1])
    except Exception as exc:  # pragma: no cover - defensive
        raise UserAuthenticationError("Challenge token subject is malformed.") from exc


async def _enforce_mfa_verify_quota(key: object, client_ip: str | None) -> None:
    settings = get_settings()
    limit = settings.mfa_verify_rate_limit_per_hour
    if limit <= 0:
        return
    quotas: list[tuple[RateLimitQuota, list[str]]] = [
        (
            RateLimitQuota(
                name="mfa_verify_user",
                limit=limit,
                window_seconds=3600,
                scope="user",
            ),
            [str(key)],
        )
    ]
    if client_ip:
        quotas.append(
            (
                RateLimitQuota(
                    name="mfa_verify_ip",
                    limit=limit * 2,
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
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(exc),
            ) from exc
