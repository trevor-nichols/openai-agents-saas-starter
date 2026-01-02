"""SSO configuration helpers and validation."""

from __future__ import annotations

from urllib.parse import urlencode

from app.core.settings import Settings
from app.domain.sso import SsoProviderConfig, SsoTokenAuthMethod

from .errors import SsoConfigurationError
from .oidc_client import OidcDiscoveryDocument

_DEFAULT_SCOPES = ["openid", "email", "profile"]
_SAFE_ID_TOKEN_ALGS = {
    "RS256",
    "RS384",
    "RS512",
    "PS256",
    "PS384",
    "PS512",
    "ES256",
    "ES384",
    "ES512",
}


def normalize_provider_key(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        raise SsoConfigurationError(
            "SSO provider key is required.",
            reason="provider_required",
        )
    return normalized


def resolve_scopes(scopes: list[str]) -> list[str]:
    resolved = [scope.strip() for scope in scopes if scope and scope.strip()]
    if not resolved:
        resolved = list(_DEFAULT_SCOPES)
    if "openid" not in resolved:
        resolved.insert(0, "openid")
    return resolved


def build_authorize_url(
    base_url: str,
    *,
    client_id: str,
    redirect_uri: str,
    scopes: list[str],
    state: str,
    nonce: str,
    code_challenge: str | None,
    login_hint: str | None,
) -> str:
    params: dict[str, str] = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state,
        "nonce": nonce,
    }
    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"
    if login_hint:
        params["login_hint"] = login_hint
    return f"{base_url}?{urlencode(params)}"


def default_redirect_uri(settings: Settings, *, provider_key: str) -> str:
    base = (settings.app_public_url or "http://localhost:3000").strip().rstrip("/")
    return f"{base}/auth/sso/{provider_key}/callback"


def resolve_token_auth_method(
    config: SsoProviderConfig, discovery: OidcDiscoveryDocument
) -> SsoTokenAuthMethod:
    method = config.token_endpoint_auth_method
    supported = getattr(discovery, "token_endpoint_auth_methods_supported", None)
    if supported:
        normalized_supported = {
            str(item).strip().lower() for item in supported if str(item).strip()
        }
        if method.value not in normalized_supported:
            raise SsoConfigurationError(
                "Token endpoint auth method is not supported by provider.",
                reason="token_auth_method_unsupported",
            )
    if method in {
        SsoTokenAuthMethod.CLIENT_SECRET_BASIC,
        SsoTokenAuthMethod.CLIENT_SECRET_POST,
    } and not config.client_secret:
        raise SsoConfigurationError(
            "Client secret is required for token endpoint authentication.",
            reason="client_secret_required",
        )
    if method == SsoTokenAuthMethod.NONE and not config.pkce_required:
        raise SsoConfigurationError(
            "Public clients must require PKCE.",
            reason="pkce_required_for_public_client",
        )
    return method


def normalize_alg_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    normalized: list[str] = []
    for value in values:
        if not value:
            continue
        alg = str(value).strip().upper()
        if alg:
            normalized.append(alg)
    return normalized


def resolve_allowed_id_token_algs(
    config: SsoProviderConfig, discovery: OidcDiscoveryDocument
) -> list[str]:
    configured = normalize_alg_list(config.allowed_id_token_algs)
    supported_raw = getattr(discovery, "id_token_signing_alg_values_supported", None)
    supported = normalize_alg_list(list(supported_raw) if supported_raw else [])

    if configured:
        configured = [alg for alg in configured if alg in _SAFE_ID_TOKEN_ALGS]
        if not configured:
            raise SsoConfigurationError(
                "Allowed ID token algorithms are invalid.",
                reason="id_token_alg_invalid",
            )
        if supported:
            unsupported = [alg for alg in configured if alg not in supported]
            if unsupported:
                raise SsoConfigurationError(
                    "Allowed ID token algorithms are not supported by provider.",
                    reason="id_token_alg_unsupported",
                )
        return configured

    if supported:
        allowed = [alg for alg in supported if alg in _SAFE_ID_TOKEN_ALGS]
        if not allowed:
            raise SsoConfigurationError(
                "Provider does not advertise supported asymmetric ID token algorithms.",
                reason="id_token_alg_unsupported",
            )
        return allowed

    return ["RS256"]


def email_domain_allowed(email: str, allowlist: list[str]) -> bool:
    if not allowlist:
        return False
    domain = email.split("@")[-1].lower()
    for allowed in allowlist:
        normalized = allowed.strip().lower().lstrip("@")
        if not normalized:
            continue
        if domain == normalized:
            return True
        if domain.endswith(f".{normalized}"):
            return True
    return False


__all__ = [
    "build_authorize_url",
    "default_redirect_uri",
    "email_domain_allowed",
    "normalize_alg_list",
    "normalize_provider_key",
    "resolve_allowed_id_token_algs",
    "resolve_scopes",
    "resolve_token_auth_method",
]
