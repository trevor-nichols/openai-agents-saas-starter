"""SSO endpoints for OIDC providers."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.api.dependencies import raise_rate_limit_http_error
from app.api.models.auth import (
    SsoCallbackRequest,
    SsoProviderListResponse,
    SsoProviderView,
    SsoStartRequest,
    SsoStartResponse,
    UserSessionResponse,
)
from app.api.models.mfa import MfaChallengeResponse
from app.api.v1.auth.utils import (
    extract_client_ip,
    extract_user_agent,
    map_user_auth_error,
    to_mfa_challenge_response,
    to_user_session_response,
)
from app.core.settings import get_settings
from app.domain.sso import SsoProviderConfig
from app.services.auth_service import MfaRequiredError, UserAuthenticationError
from app.services.shared.rate_limit_service import (
    RateLimitExceeded,
    RateLimitQuota,
    rate_limiter,
)
from app.services.sso import (
    SsoConfigurationError,
    SsoIdentityError,
    SsoProvisioningError,
    SsoService,
    SsoServiceError,
    SsoStateError,
    SsoTokenError,
    get_sso_service,
)

router = APIRouter(tags=["auth"])


def _sso_service() -> SsoService:
    return get_sso_service()


@router.get("/sso/providers", response_model=SsoProviderListResponse)
async def list_sso_providers(
    tenant_id: str | None = Query(default=None),
    tenant_slug: str | None = Query(default=None),
    service: SsoService = Depends(_sso_service),
) -> SsoProviderListResponse:
    if bool(tenant_id) == bool(tenant_slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide exactly one of tenant_id or tenant_slug.",
        )
    resolved_tenant_id = _parse_optional_uuid(tenant_id)
    try:
        providers = await service.list_providers(
            tenant_id=resolved_tenant_id,
            tenant_slug=tenant_slug,
        )
    except SsoServiceError as exc:
        raise _map_sso_error(exc) from exc

    views = [_to_provider_view(item) for item in providers]
    return SsoProviderListResponse(providers=views)


@router.post("/sso/{provider}/start", response_model=SsoStartResponse)
async def start_sso(
    provider: str,
    payload: SsoStartRequest,
    request: Request,
    service: SsoService = Depends(_sso_service),
) -> SsoStartResponse:
    if payload.tenant_id and payload.tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide only one of tenant_id or tenant_slug.",
        )
    if not payload.tenant_id and not payload.tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenant selection is required for SSO.",
        )
    resolved_tenant_id = _parse_optional_uuid(payload.tenant_id)
    client_ip = extract_client_ip(request)
    await _enforce_sso_start_quota(
        tenant_id=resolved_tenant_id,
        tenant_slug=payload.tenant_slug,
        provider_key=provider,
        client_ip=client_ip,
    )
    try:
        result = await service.start_sso(
            provider_key=provider,
            tenant_id=resolved_tenant_id,
            tenant_slug=payload.tenant_slug,
            login_hint=payload.login_hint,
        )
    except SsoServiceError as exc:
        raise _map_sso_error(exc) from exc

    return SsoStartResponse(authorize_url=result.authorize_url)


@router.post(
    "/sso/{provider}/callback",
    response_model=UserSessionResponse | MfaChallengeResponse,
    responses={
        status.HTTP_202_ACCEPTED: {
            "model": MfaChallengeResponse,
            "description": "MFA required; challenge token and available methods returned.",
        }
    },
)
async def complete_sso(
    provider: str,
    payload: SsoCallbackRequest,
    request: Request,
    response: Response,
    service: SsoService = Depends(_sso_service),
) -> UserSessionResponse | MfaChallengeResponse:
    client_ip = extract_client_ip(request)
    user_agent = extract_user_agent(request)
    await _enforce_sso_callback_quota(provider_key=provider, client_ip=client_ip)

    try:
        tokens = await service.complete_sso(
            provider_key=provider,
            code=payload.code,
            state=payload.state,
            ip_address=client_ip,
            user_agent=user_agent,
        )
    except MfaRequiredError as exc:
        response.status_code = status.HTTP_202_ACCEPTED
        return to_mfa_challenge_response(exc)
    except UserAuthenticationError as exc:
        raise map_user_auth_error(exc) from exc
    except SsoServiceError as exc:
        raise _map_sso_error(exc) from exc

    return to_user_session_response(tokens)


def _to_provider_view(config: SsoProviderConfig) -> SsoProviderView:
    display = _provider_display_name(config.provider_key)
    return SsoProviderView(provider_key=config.provider_key, display_name=display)


def _provider_display_name(provider_key: str) -> str:
    normalized = provider_key.strip().lower()
    mapping = {
        "google": "Google",
        "microsoft": "Microsoft",
        "azure": "Microsoft",
        "okta": "Okta",
        "auth0": "Auth0",
    }
    if normalized in mapping:
        return mapping[normalized]
    return provider_key.replace("_", " ").strip().title() or provider_key


async def _enforce_sso_start_quota(
    *,
    tenant_id: UUID | None,
    tenant_slug: str | None,
    provider_key: str,
    client_ip: str | None,
) -> None:
    settings = get_settings()
    limit = settings.sso_start_rate_limit_per_minute
    if limit <= 0:
        return
    provider = provider_key.strip().lower() or "unknown"
    tenant_scope = str(tenant_id or tenant_slug or "unknown")
    quotas: list[tuple[RateLimitQuota, list[str]]] = [
        (
            RateLimitQuota(
                name="sso_start_tenant",
                limit=limit,
                window_seconds=60,
                scope="tenant",
            ),
            [tenant_scope, provider],
        )
    ]
    if client_ip:
        quotas.append(
            (
                RateLimitQuota(
                    name="sso_start_ip",
                    limit=limit * 2,
                    window_seconds=60,
                    scope="ip",
                ),
                [client_ip, provider],
            )
        )
    for quota, keys in quotas:
        try:
            await rate_limiter.enforce(quota, keys)
        except RateLimitExceeded as exc:
            raise_rate_limit_http_error(exc, tenant_id=tenant_scope)


async def _enforce_sso_callback_quota(*, provider_key: str, client_ip: str | None) -> None:
    settings = get_settings()
    limit = settings.sso_callback_rate_limit_per_minute
    if limit <= 0:
        return
    provider = provider_key.strip().lower() or "unknown"
    key = client_ip or "unknown"
    quota = RateLimitQuota(
        name="sso_callback_ip",
        limit=limit,
        window_seconds=60,
        scope="ip",
    )
    try:
        await rate_limiter.enforce(quota, [key, provider])
    except RateLimitExceeded as exc:
        raise_rate_limit_http_error(exc, tenant_id=None)


def _map_sso_error(exc: SsoServiceError) -> HTTPException:
    if isinstance(exc, SsoStateError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, SsoTokenError):
        if exc.reason in {"token_verification_failed"}:
            return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
        if exc.reason in {
            "discovery_failed",
            "token_exchange_failed",
            "token_handling_failed",
            "discovery_missing",
        }:
            return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, SsoProvisioningError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, SsoIdentityError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, SsoConfigurationError):
        if exc.reason in {"discovery_failed"}:
            return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
        if exc.reason in {"provider_disabled", "provider_not_configured"}:
            return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
        if exc.reason in {
            "token_auth_method_unsupported",
            "client_secret_required",
            "pkce_required_for_public_client",
            "id_token_alg_invalid",
            "id_token_alg_unsupported",
        }:
            return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
        if exc.reason in {"tenant_required", "tenant_not_found"}:
            return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
        if exc.reason in {"tenant_invalid"}:
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


def _parse_optional_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id must be a valid UUID.",
        ) from exc


__all__ = ["router"]
