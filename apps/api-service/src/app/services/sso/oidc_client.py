"""OIDC discovery, token exchange, and ID token verification helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from jwt import PyJWTError


class OidcError(RuntimeError):
    """Base class for OIDC failures."""


class OidcDiscoveryError(OidcError):
    """Raised when discovery metadata cannot be retrieved or parsed."""


class OidcTokenExchangeError(OidcError):
    """Raised when the token endpoint returns an error."""


class OidcTokenVerificationError(OidcError):
    """Raised when ID token verification fails."""


@dataclass(slots=True)
class OidcDiscoveryDocument:
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    id_token_signing_alg_values_supported: list[str] | None = None
    token_endpoint_auth_methods_supported: list[str] | None = None


@dataclass(slots=True)
class OidcTokenResponse:
    id_token: str
    access_token: str | None
    refresh_token: str | None
    expires_in: int | None
    token_type: str | None
    scope: str | None


class OidcClient:
    """Minimal async OIDC client with discovery and ID token verification."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=10)
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def fetch_discovery(
        self,
        issuer_url: str,
        *,
        discovery_url: str | None = None,
    ) -> OidcDiscoveryDocument:
        url = discovery_url or issuer_url.rstrip("/") + "/.well-known/openid-configuration"
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcDiscoveryError("Failed to fetch OIDC discovery document.") from exc
        if not isinstance(payload, dict):
            raise OidcDiscoveryError("OIDC discovery document was not a JSON object.")

        def _require_str(key: str) -> str:
            value = payload.get(key)
            if not isinstance(value, str) or not value.strip():
                raise OidcDiscoveryError(f"OIDC discovery document missing '{key}'.")
            return value.strip()

        def _optional_str_list(key: str) -> list[str] | None:
            value = payload.get(key)
            if value is None:
                return None
            if not isinstance(value, list):
                raise OidcDiscoveryError(f"OIDC discovery document '{key}' is invalid.")
            items = [str(item).strip() for item in value if str(item).strip()]
            return items or None

        issuer = payload.get("issuer") or issuer_url
        if not isinstance(issuer, str) or not issuer.strip():
            raise OidcDiscoveryError("OIDC discovery document missing 'issuer'.")

        return OidcDiscoveryDocument(
            issuer=issuer.strip(),
            authorization_endpoint=_require_str("authorization_endpoint"),
            token_endpoint=_require_str("token_endpoint"),
            jwks_uri=_require_str("jwks_uri"),
            id_token_signing_alg_values_supported=_optional_str_list(
                "id_token_signing_alg_values_supported"
            ),
            token_endpoint_auth_methods_supported=_optional_str_list(
                "token_endpoint_auth_methods_supported"
            ),
        )

    async def exchange_code_for_tokens(
        self,
        *,
        token_endpoint: str,
        client_id: str,
        client_secret: str | None,
        code: str,
        redirect_uri: str,
        code_verifier: str | None,
        token_auth_method: str,
    ) -> OidcTokenResponse:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        auth: tuple[str, str] | None = None
        method = token_auth_method.strip().lower()
        if method == "client_secret_basic":
            if not client_secret:
                raise OidcTokenExchangeError("client_secret is required for basic auth.")
            auth = (client_id, client_secret)
        elif method == "client_secret_post":
            if not client_secret:
                raise OidcTokenExchangeError("client_secret is required for post auth.")
            data["client_id"] = client_id
            data["client_secret"] = client_secret
        elif method == "none":
            data["client_id"] = client_id
            auth = None
        else:
            raise OidcTokenExchangeError("Unsupported token auth method.")
        try:
            request_kwargs: dict[str, Any] = {"data": data}
            if auth is not None:
                request_kwargs["auth"] = auth
            response = await self._client.post(token_endpoint, **request_kwargs)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcTokenExchangeError("OIDC token exchange failed.") from exc

        if "id_token" not in payload:
            raise OidcTokenExchangeError("OIDC token response missing id_token.")

        return OidcTokenResponse(
            id_token=str(payload.get("id_token")),
            access_token=payload.get("access_token"),
            refresh_token=payload.get("refresh_token"),
            expires_in=payload.get("expires_in"),
            token_type=payload.get("token_type"),
            scope=payload.get("scope"),
        )

    async def verify_id_token(
        self,
        *,
        id_token: str,
        issuer: str,
        audience: str,
        jwks_uri: str,
        allowed_algs: list[str] | None = None,
        clock_skew_seconds: int = 60,
    ) -> Mapping[str, Any]:
        try:
            header = jwt.get_unverified_header(id_token)
        except PyJWTError as exc:
            raise OidcTokenVerificationError("Invalid ID token header.") from exc
        kid = header.get("kid")
        alg = header.get("alg")
        if not kid or not alg:
            raise OidcTokenVerificationError("ID token missing kid/alg.")
        if not isinstance(alg, str) or not alg.strip():
            raise OidcTokenVerificationError("ID token algorithm is invalid.")
        alg = alg.strip().upper()
        allowed = [
            str(item).strip().upper() for item in (allowed_algs or []) if str(item).strip()
        ]
        if not allowed:
            raise OidcTokenVerificationError("No allowed ID token algorithms configured.")
        if alg not in allowed:
            raise OidcTokenVerificationError("ID token algorithm is not allowed.")

        jwks = await self._fetch_jwks(jwks_uri)
        key = self._select_key(jwks, kid)
        if not key:
            raise OidcTokenVerificationError("Matching JWKS key not found.")

        try:
            algorithms = jwt.algorithms.get_default_algorithms()
            algorithm = algorithms.get(alg)
            if algorithm is None:
                raise OidcTokenVerificationError("ID token algorithm is unsupported.")
            public_key = algorithm.from_jwk(json.dumps(key))
            return jwt.decode(
                id_token,
                public_key,
                algorithms=allowed,
                audience=audience,
                issuer=issuer,
                leeway=clock_skew_seconds,
                options={"require": ["exp", "iat"]},
            )
        except PyJWTError as exc:
            raise OidcTokenVerificationError("ID token verification failed.") from exc

    async def _fetch_jwks(self, jwks_uri: str) -> Mapping[str, Any]:
        try:
            response = await self._client.get(jwks_uri)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcTokenVerificationError("Failed to fetch JWKS.") from exc
        if not isinstance(payload, dict) or "keys" not in payload:
            raise OidcTokenVerificationError("JWKS payload is invalid.")
        return payload

    @staticmethod
    def _select_key(jwks: Mapping[str, Any], kid: str) -> dict[str, Any] | None:
        keys = jwks.get("keys")
        if not isinstance(keys, list):
            return None
        for key in keys:
            if isinstance(key, dict) and key.get("kid") == kid:
                return key
        return None


__all__ = [
    "OidcClient",
    "OidcDiscoveryDocument",
    "OidcError",
    "OidcDiscoveryError",
    "OidcTokenExchangeError",
    "OidcTokenResponse",
    "OidcTokenVerificationError",
]
