"""Authentication endpoints for API v1."""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool

from app.api.dependencies.auth import require_current_user
from app.api.models.auth import (
    ServiceAccountIssueRequest,
    ServiceAccountTokenResponse,
    UserLoginRequest,
    UserRefreshRequest,
    UserSessionResponse,
)
from app.api.models.common import SuccessResponse
from app.core.config import get_settings
from app.infrastructure.security.nonce_store import get_nonce_store
from app.infrastructure.security.vault import (
    VaultClientUnavailable,
    VaultVerificationError,
    get_vault_transit_client,
)
from app.observability.logging import log_event
from app.observability.metrics import record_nonce_cache_result
from app.services.auth_service import (
    ServiceAccountCatalogUnavailable,
    ServiceAccountRateLimitError,
    ServiceAccountValidationError,
    UserAuthenticationError,
    UserRefreshError,
    UserSessionTokens,
    auth_service,
)
from app.services.user_service import (
    InvalidCredentialsError,
    MembershipNotFoundError,
    TenantContextRequiredError,
    UserDisabledError,
    UserLockedError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=UserSessionResponse)
async def login_for_access_token(
    payload: UserLoginRequest,
    request: Request,
) -> UserSessionResponse:
    """Authenticate a user and mint fresh access/refresh tokens."""

    client_ip = _extract_client_ip(request)
    user_agent = _extract_user_agent(request)

    try:
        tokens = await auth_service.login_user(
            email=payload.email,
            password=payload.password,
            tenant_id=payload.tenant_id or None,
            ip_address=client_ip,
            user_agent=user_agent,
        )
    except UserAuthenticationError as exc:
        raise _map_user_auth_error(exc) from exc

    return _to_user_session_response(tokens)


@router.post("/refresh", response_model=UserSessionResponse)
async def refresh_access_token(
    payload: UserRefreshRequest,
    request: Request,
) -> UserSessionResponse:
    """Exchange a refresh token for a new access/refresh pair."""

    client_ip = _extract_client_ip(request)
    user_agent = _extract_user_agent(request)

    try:
        tokens = await auth_service.refresh_user_session(
            payload.refresh_token,
            ip_address=client_ip,
            user_agent=user_agent,
        )
    except (InvalidCredentialsError, MembershipNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except UserRefreshError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except UserLockedError as exc:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(exc)) from exc
    except UserDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return _to_user_session_response(tokens)


@router.get("/me", response_model=SuccessResponse)
async def get_current_user_info(
    current_user: dict[str, Any] = Depends(require_current_user),
) -> SuccessResponse:
    """Return metadata about the current authenticated user."""

    return SuccessResponse(
        message="User information retrieved successfully",
        data={
            "user_id": current_user["user_id"],
            "token_payload": current_user["payload"],
        },
    )


def _extract_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip() or None
    if request.client and request.client.host:
        return request.client.host
    return None


def _extract_user_agent(request: Request) -> str | None:
    header = request.headers.get("user-agent")
    return header.strip() if header else None


def _to_user_session_response(tokens: UserSessionTokens) -> UserSessionResponse:
    return UserSessionResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_at=tokens.expires_at,
        refresh_expires_at=tokens.refresh_expires_at,
        kid=tokens.kid,
        refresh_kid=tokens.refresh_kid,
        scopes=tokens.scopes,
        tenant_id=tokens.tenant_id,
        user_id=tokens.user_id,
    )


def _map_user_auth_error(exc: UserAuthenticationError) -> HTTPException:
    cause = exc.__cause__
    if isinstance(cause, InvalidCredentialsError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(cause),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if isinstance(cause, UserLockedError):
        return HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(cause))
    if isinstance(cause, UserDisabledError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(cause))
    if isinstance(cause, TenantContextRequiredError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(cause))
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=str(exc),
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post(
    "/service-accounts/issue",
    response_model=ServiceAccountTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def issue_service_account_token(
    payload: ServiceAccountIssueRequest,
    authorization: str = Header(..., alias="Authorization"),
    vault_payload: str | None = Header(default=None, alias="X-Vault-Payload"),
) -> ServiceAccountTokenResponse:
    """Mint a refresh token for a registered service account."""

    credential_type = require_vault_signature(authorization, vault_payload)

    try:
        claims = await _validate_vault_payload(
            credential_type=credential_type,
            authorization=authorization,
            vault_payload=vault_payload,
            request_payload=payload,
        )

        result = await auth_service.issue_service_account_refresh_token(
            account=payload.account,
            scopes=payload.scopes,
            tenant_id=payload.tenant_id,
            requested_ttl_minutes=payload.lifetime_minutes,
            fingerprint=payload.fingerprint,
            force=payload.force,
        )
    except ServiceAccountValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ServiceAccountRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except ServiceAccountCatalogUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    if claims is not None:
        _validate_request_against_claims(claims, payload)

    return ServiceAccountTokenResponse.model_validate(result)


def _vault_verification_enabled() -> bool:
    settings = get_settings()
    return settings.vault_verify_enabled


def require_vault_signature(header_value: str, vault_payload: str | None) -> str:
    if not header_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )

    if not header_value.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must use Bearer scheme.",
        )

    credential = header_value[7:].strip()

    if credential.startswith("vault:"):
        if not vault_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-Vault-Payload header.",
            )
        return "vault"

    if credential == "dev-local" and not _vault_verification_enabled():
        # Local/testing escape hatch when Vault integration is disabled.
        return "dev-local"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Vault-signed credential required for service-account issuance.",
    )


async def _validate_vault_payload(
    *,
    credential_type: str,
    authorization: str,
    vault_payload: str | None,
    request_payload: ServiceAccountIssueRequest,
) -> dict[str, Any] | None:
    if credential_type != "vault":
        return None

    assert vault_payload is not None  # satisfied by require_vault_signature

    claims = _decode_vault_payload(vault_payload)
    _validate_claims_shape(claims)
    _validate_claims_against_request(claims, request_payload)

    if _vault_verification_enabled():
        await _verify_vault_signature(authorization, vault_payload)

    await _enforce_nonce(claims)
    _enforce_timestamps(claims)
    return claims


async def _verify_vault_signature(authorization: str, vault_payload: str) -> None:
    signature = _extract_signature(authorization)

    try:
        client = get_vault_transit_client()
    except VaultClientUnavailable as exc:
        log_event(
            "vault_signature_verify",
            level="error",
            result="error",
            reason="client_unavailable",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vault client not configured.",
        ) from exc

    try:
        valid = await run_in_threadpool(client.verify_signature, vault_payload, signature)
    except VaultVerificationError as exc:
        log_event(
            "vault_signature_verify",
            level="error",
            result="error",
            reason="verification_exception",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Vault verification failed: {exc}",
        ) from exc

    if not valid:
        log_event(
            "vault_signature_verify",
            level="warning",
            result="failure",
            reason="invalid_signature",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Vault signature.",
        )
    log_event(
        "vault_signature_verify",
        result="success",
        reason="validated",
    )


async def _enforce_nonce(claims: dict[str, Any]) -> None:
    nonce = claims.get("nonce")
    if not isinstance(nonce, str) or not nonce.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault payload missing nonce.",
        )

    exp = claims.get("exp")
    if not isinstance(exp, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault payload missing exp.",
        )

    now = datetime.now(UTC)
    ttl_seconds = exp - int(now.timestamp())
    if ttl_seconds <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault payload expired.",
        )

    ttl_seconds = min(ttl_seconds, 300)  # constrain TTL to 5 minutes

    nonce_store = get_nonce_store()
    is_new = await nonce_store.check_and_store(nonce, ttl_seconds)
    record_nonce_cache_result(hit=not is_new)
    if not is_new:
        log_event(
            "vault_nonce_cache",
            level="warning",
            result="hit",
            reason="nonce_reuse",
            nonce_digest=_digest_nonce(nonce),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault payload nonce already used.",
        )
    log_event(
        "vault_nonce_cache",
        result="miss",
        reason="nonce_accepted",
        nonce_digest=_digest_nonce(nonce),
    )


def _enforce_timestamps(claims: dict[str, Any]) -> None:
    issued_at = claims.get("iat")
    if not isinstance(issued_at, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault payload missing iat.",
        )

    now = datetime.now(UTC)
    issued_delta = now.timestamp() - issued_at
    if issued_delta < -30:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault payload iat is in the future.",
        )
    if issued_delta > 600:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault payload iat outside acceptable window.",
        )


def _validate_claims_against_request(
    claims: dict[str, Any], request_payload: ServiceAccountIssueRequest
) -> None:
    account = claims.get("account")
    if account != request_payload.account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vault payload account mismatch.",
        )

    tenant_id = claims.get("tenant_id")
    if request_payload.tenant_id and tenant_id != request_payload.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vault payload tenant mismatch.",
        )

    signed_scopes = _normalize_scope_list(
        claims.get("scopes"),
        field_name="Vault payload scopes",
        error_status=status.HTTP_401_UNAUTHORIZED,
    )
    requested_scopes = _normalize_scope_list(
        request_payload.scopes,
        field_name="Request scopes",
        error_status=status.HTTP_400_BAD_REQUEST,
    )
    if set(requested_scopes) != set(signed_scopes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vault payload scopes mismatch.",
        )
    # Normalize ordering to the signed payload to prevent scope reordering attacks downstream.
    request_payload.scopes = signed_scopes

    signed_ttl = claims.get("lifetime_minutes")
    request_ttl = request_payload.lifetime_minutes
    if request_ttl is not None and signed_ttl is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vault payload missing lifetime_minutes.",
        )
    if signed_ttl is not None:
        ttl_minutes = _coerce_positive_int(
            signed_ttl,
            field_name="Vault payload lifetime_minutes",
            error_status=status.HTTP_401_UNAUTHORIZED,
        )
        if request_ttl is None:
            request_payload.lifetime_minutes = ttl_minutes
        elif request_ttl != ttl_minutes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vault payload lifetime_minutes mismatch.",
            )

    signed_fingerprint = claims.get("fingerprint")
    request_fingerprint = request_payload.fingerprint
    if request_fingerprint and not signed_fingerprint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vault payload missing fingerprint.",
        )
    if signed_fingerprint is not None:
        if not isinstance(signed_fingerprint, str) or not signed_fingerprint.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Vault payload fingerprint invalid.",
            )
        if request_fingerprint and request_fingerprint != signed_fingerprint:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vault payload fingerprint mismatch.",
            )
        request_payload.fingerprint = signed_fingerprint


def _validate_request_against_claims(
    claims: dict[str, Any],
    request_payload: ServiceAccountIssueRequest,
) -> None:
    # Currently we enforce account/tenant parity pre-issuance; the post-issuance hook
    # is retained to simplify future auditing (e.g., logging request metadata).
    _validate_claims_against_request(claims, request_payload)


def _extract_signature(authorization: str) -> str:
    credential = authorization[7:].strip()
    if credential.lower().startswith("vault:"):
        return credential.split(":", 1)[1]
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authorization header missing Vault credential.",
    )


def _decode_vault_payload(vault_payload: str) -> dict[str, Any]:
    padded = vault_payload + "=" * (-len(vault_payload) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Vault payload encoding: {exc}",
        ) from exc

    try:
        data = json.loads(decoded)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Vault payload JSON: {exc}",
        ) from exc

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unexpected Vault payload shape.",
        )
    return data


def _digest_nonce(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _validate_claims_shape(claims: dict[str, Any]) -> None:
    required_fields = {"iss", "aud", "sub", "nonce", "iat", "exp", "account", "scopes"}
    missing = [field for field in required_fields if field not in claims]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Vault payload missing fields: {', '.join(missing)}",
        )

    if not isinstance(claims.get("aud"), list) or "auth-service" not in claims["aud"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault payload audience invalid.",
        )

    if not isinstance(claims.get("scopes"), list):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault payload scopes must be a list.",
        )


def _normalize_scope_list(
    scopes: Any,
    *,
    field_name: str,
    error_status: int,
) -> list[str]:
    if not isinstance(scopes, list):
        raise HTTPException(
            status_code=error_status, detail=f"{field_name} must be an array of strings."
        )

    normalized: list[str] = []
    for scope in scopes:
        if not isinstance(scope, str):
            raise HTTPException(
                status_code=error_status, detail=f"{field_name} must contain strings only."
            )
        trimmed = scope.strip()
        if not trimmed:
            raise HTTPException(
                status_code=error_status, detail=f"{field_name} cannot contain empty scopes."
            )
        if trimmed not in normalized:
            normalized.append(trimmed)

    if not normalized:
        raise HTTPException(
            status_code=error_status, detail=f"{field_name} must include at least one scope."
        )
    return normalized


def _coerce_positive_int(value: Any, *, field_name: str, error_status: int) -> int:
    if not isinstance(value, int) or value <= 0:
        raise HTTPException(
            status_code=error_status, detail=f"{field_name} must be a positive integer."
        )
    return value
