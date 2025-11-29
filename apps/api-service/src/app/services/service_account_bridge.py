"""Browser-friendly service-account issuance bridge."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any, Protocol
from uuid import uuid4

from fastapi import status

from app.api.dependencies.service_accounts import ServiceAccountActor, ServiceAccountActorType
from app.api.models.auth import BrowserServiceAccountIssueRequest
from app.domain.secrets import SecretProviderProtocol, SecretPurpose
from app.infrastructure.secrets import get_secret_provider
from app.infrastructure.security.vault import VaultClientUnavailable, VaultSigningError
from app.observability.logging import log_event
from app.services.auth.errors import (
    ServiceAccountCatalogUnavailable,
    ServiceAccountError,
    ServiceAccountRateLimitError,
    ServiceAccountValidationError,
)
from app.services.auth_service import auth_service

_BROWSER_SUBJECT = "service-account-browser"
_BROWSER_AUDIENCE = ["auth-service"]
_CLAIM_TTL = timedelta(minutes=5)


class BrowserIssuanceError(RuntimeError):
    """Raised when browser-driven issuance cannot proceed."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(slots=True)
class SignedVaultPayload:
    payload_b64: str
    signature: str


class ServiceAccountSigner(Protocol):
    async def sign(self, payload: dict[str, Any]) -> SignedVaultPayload:
        """Sign the structured payload and return Vault signature metadata."""
        ...


class SecretProviderSigner(ServiceAccountSigner):
    """Signs payloads via the configured SecretProvider."""

    def __init__(self) -> None:
        self._provider: SecretProviderProtocol | None = None

    async def sign(self, payload: dict[str, Any]) -> SignedVaultPayload:
        provider = self._get_provider()
        payload_bytes = _serialize_payload(payload)
        payload_b64 = _encode_payload_bytes(payload_bytes)
        signed = await provider.sign(
            payload_bytes,
            purpose=SecretPurpose.SERVICE_ACCOUNT_ISSUANCE,
        )
        payload_b64 = signed.metadata.get("payload_b64") or payload_b64
        return SignedVaultPayload(payload_b64=payload_b64, signature=signed.signature)

    def _get_provider(self) -> SecretProviderProtocol:
        if self._provider is None:
            self._provider = get_secret_provider()
        return self._provider


class ServiceAccountIssuanceBridge:
    """Coordinates Vault signing + auth-service issuance for browser clients."""

    def __init__(self, signer: ServiceAccountSigner | None = None) -> None:
        self._signer = signer or SecretProviderSigner()

    async def issue_from_browser(
        self,
        *,
        actor: ServiceAccountActor,
        request: BrowserServiceAccountIssueRequest,
    ) -> dict[str, Any]:
        reason = request.reason.strip() if request.reason else ""
        if not reason:
            raise BrowserIssuanceError("Reason is required for auditing.")

        tenant_id = self._resolve_tenant_scope(actor=actor, request=request)
        claims = self._build_claims(
            actor=actor,
            request=request,
            tenant_id=tenant_id,
            reason=reason,
        )
        try:
            signed = await self._signer.sign(claims)
        except VaultClientUnavailable as exc:  # pragma: no cover - network/config
            raise BrowserIssuanceError(
                "Vault Transit client is not configured.", status.HTTP_503_SERVICE_UNAVAILABLE
            ) from exc
        except (VaultSigningError, RuntimeError) as exc:
            raise BrowserIssuanceError(
                "Vault Transit signing failed.", status.HTTP_503_SERVICE_UNAVAILABLE
            ) from exc

        log_event(
            "service_account_browser_issue",
            stage="sign",
            result="pending",
            account=request.account,
            tenant_id=tenant_id,
            user_id=_extract_user_id(actor.user),
            reason=reason,
        )

        try:
            result = await auth_service.issue_service_account_refresh_token(
                account=request.account,
                scopes=request.scopes,
                tenant_id=tenant_id,
                requested_ttl_minutes=request.lifetime_minutes,
                fingerprint=request.fingerprint,
                force=request.force,
            )
        except ServiceAccountValidationError as exc:
            raise BrowserIssuanceError(str(exc), status.HTTP_400_BAD_REQUEST) from exc
        except ServiceAccountRateLimitError as exc:
            raise BrowserIssuanceError(str(exc), status.HTTP_429_TOO_MANY_REQUESTS) from exc
        except ServiceAccountCatalogUnavailable as exc:
            raise BrowserIssuanceError(str(exc), status.HTTP_503_SERVICE_UNAVAILABLE) from exc
        except ServiceAccountError as exc:
            raise BrowserIssuanceError(
                "Failed to issue service-account token.", status.HTTP_503_SERVICE_UNAVAILABLE
            ) from exc

        log_event(
            "service_account_browser_issue",
            stage="issue",
            result="success",
            account=request.account,
            tenant_id=tenant_id,
            user_id=_extract_user_id(actor.user),
            reason=reason,
            signature=signed.signature,
        )
        return result

    def _build_claims(
        self,
        *,
        actor: ServiceAccountActor,
        request: BrowserServiceAccountIssueRequest,
        tenant_id: str | None,
        reason: str,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        expires = now + _CLAIM_TTL
        return {
            "iss": "vault-transit",
            "aud": _BROWSER_AUDIENCE,
            "sub": _BROWSER_SUBJECT,
            "nonce": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "account": request.account,
            "tenant_id": tenant_id,
            "scopes": request.scopes,
            "lifetime_minutes": request.lifetime_minutes,
            "fingerprint": request.fingerprint,
            "reason": reason,
            "actor": {
                "user_id": _extract_user_id(actor.user),
                "tenant_id": actor.tenant_id,
                "role": actor.actor_type.value,
            },
        }

    def _resolve_tenant_scope(
        self,
        *,
        actor: ServiceAccountActor,
        request: BrowserServiceAccountIssueRequest,
    ) -> str | None:
        if actor.actor_type is ServiceAccountActorType.PLATFORM_OPERATOR:
            return request.tenant_id

        actor_tenant_id = actor.tenant_id
        if not actor_tenant_id:
            raise BrowserIssuanceError(
                "Tenant context is required for admin-issued service-account tokens.",
                status.HTTP_403_FORBIDDEN,
            )

        requested_tenant_id = request.tenant_id
        if requested_tenant_id is None:
            return actor_tenant_id
        if requested_tenant_id != actor_tenant_id:
            raise BrowserIssuanceError(
                "Tenant mismatch for service-account issuance.",
                status.HTTP_403_FORBIDDEN,
            )
        return actor_tenant_id


def _serialize_payload(payload: dict[str, Any]) -> bytes:
    document = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return document.encode("utf-8")


def _encode_payload_bytes(payload: bytes) -> str:
    encoded = base64.urlsafe_b64encode(payload).decode("ascii")
    return encoded.rstrip("=")


def _extract_user_id(user: dict[str, Any]) -> str | None:
    if not isinstance(user, dict):
        return None
    payload = user.get("payload")
    if isinstance(payload, dict):
        subject = payload.get("sub") or payload.get("user_id")
        if isinstance(subject, str):
            return subject
    subject = user.get("sub")
    if isinstance(subject, str):
        return subject
    return None


@lru_cache(maxsize=1)
def get_service_account_issuance_bridge() -> ServiceAccountIssuanceBridge:
    return ServiceAccountIssuanceBridge()


__all__ = [
    "BrowserIssuanceError",
    "SecretProviderSigner",
    "ServiceAccountIssuanceBridge",
    "SignedVaultPayload",
    "get_service_account_issuance_bridge",
]
