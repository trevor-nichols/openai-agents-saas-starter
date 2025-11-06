"""Authentication endpoints for API v1."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.api.dependencies.auth import require_current_user
from app.api.models.auth import (
    ServiceAccountIssueRequest,
    ServiceAccountTokenResponse,
    Token,
    UserLogin,
)
from app.api.models.common import SuccessResponse
from app.core.config import get_settings
from app.core.security import create_access_token
from app.infrastructure.security.nonce_store import get_nonce_store
from app.infrastructure.security.vault import (
    VaultClientUnavailable,
    VaultTransitClient,
    get_vault_transit_client,
    VaultVerificationError,
)
from app.services.auth_service import (
    ServiceAccountCatalogUnavailable,
    ServiceAccountRateLimitError,
    ServiceAccountValidationError,
    auth_service,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login_for_access_token(credentials: UserLogin) -> Token:
    """Authenticate a demo user and return a bearer token."""

    settings = get_settings()

    if credentials.username == "demo" and credentials.password == "demo123":
        expiry = timedelta(minutes=settings.access_token_expire_minutes)
        token = create_access_token(
            data={"sub": "demo_user_id", "username": credentials.username},
            expires_delta=expiry,
        )
        return Token(access_token=token, expires_in=int(expiry.total_seconds()))

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    current_user: dict[str, Any] = Depends(require_current_user),
) -> Token:
    """Issue a fresh token for the current authenticated user."""

    settings = get_settings()
    expiry = timedelta(minutes=settings.access_token_expire_minutes)

    token = create_access_token(
        data={"sub": current_user["user_id"]},
        expires_delta=expiry,
    )
    return Token(access_token=token, expires_in=int(expiry.total_seconds()))


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
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vault client not configured.",
        ) from exc

    try:
        valid = await run_in_threadpool(client.verify_signature, vault_payload, signature)
    except VaultVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Vault verification failed: {exc}",
        ) from exc

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Vault signature.",
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

    now = datetime.now(timezone.utc)
    ttl_seconds = exp - int(now.timestamp())
    if ttl_seconds <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault payload expired.",
        )

    ttl_seconds = min(ttl_seconds, 300)  # constrain TTL to 5 minutes

    nonce_store = get_nonce_store()
    if not await nonce_store.check_and_store(nonce, ttl_seconds):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault payload nonce already used.",
        )


def _enforce_timestamps(claims: dict[str, Any]) -> None:
    issued_at = claims.get("iat")
    if not isinstance(issued_at, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault payload missing iat.",
        )

    now = datetime.now(timezone.utc)
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
    except Exception as exc:  # noqa: BLE001
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
