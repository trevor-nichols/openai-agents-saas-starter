"""SecretProvider implementation backed by HashiCorp Vault Transit."""

from __future__ import annotations

import base64
from collections.abc import Sequence
from dataclasses import dataclass

import httpx
from anyio import to_thread

from app.core.config import Settings
from app.domain.secrets import (
    SecretProviderHealth,
    SecretProviderProtocol,
    SecretProviderStatus,
    SecretPurpose,
    SecretScope,
    SignedPayload,
)
from app.infrastructure.security.vault import VaultTransitClient, VaultVerificationError


def _b64encode(data: bytes) -> str:
    """Return base64url-encoded string without padding."""

    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


@dataclass
class VaultSecretProvider(SecretProviderProtocol):
    """Bridges the SecretProvider protocol to the existing Vault Transit client."""

    client: VaultTransitClient
    health_timeout: float = 5.0

    async def get_secret(self, key: str, *, scope: SecretScope | None = None) -> str:
        raise NotImplementedError("Vault KV access is not yet implemented for SecretProvider.")

    async def get_secrets(
        self, keys: Sequence[str], *, scope: SecretScope | None = None
    ) -> dict[str, str]:
        raise NotImplementedError("Vault KV access is not yet implemented for SecretProvider.")

    async def sign(self, payload: bytes, *, purpose: SecretPurpose) -> SignedPayload:
        payload_b64 = _b64encode(payload)
        signature = await to_thread.run_sync(self.client.sign_payload, payload_b64)
        return SignedPayload(
            signature=signature,
            algorithm="vault-transit",
            metadata={"payload_b64": payload_b64},
        )

    async def verify(
        self, payload: bytes, signature: str, *, purpose: SecretPurpose
    ) -> bool:
        payload_b64 = _b64encode(payload)
        return await to_thread.run_sync(
            self.client.verify_signature,
            payload_b64,
            signature,
        )

    async def health_check(self) -> SecretProviderHealth:
        url = f"{self.client.base_url.rstrip('/')}/v1/sys/health"

        def _probe() -> tuple[int, str]:
            with httpx.Client(timeout=self.health_timeout) as session:
                response = session.get(url, headers={"X-Vault-Token": self.client.token})
                return response.status_code, response.text

        try:
            status_code, body = await to_thread.run_sync(_probe)
        except httpx.HTTPError as exc:  # pragma: no cover - defensive
            return SecretProviderHealth(
                status=SecretProviderStatus.UNAVAILABLE,
                details={"error": str(exc)},
            )

        if 200 <= status_code < 300:
            status = SecretProviderStatus.HEALTHY
        elif status_code in {429, 472, 473, 501, 503}:
            status = SecretProviderStatus.DEGRADED
        else:
            status = SecretProviderStatus.UNAVAILABLE

        return SecretProviderHealth(
            status=status,
            details={"status_code": status_code, "body": body[:200]},
        )


def build_vault_secret_provider(settings: Settings) -> SecretProviderProtocol:
    config = settings.vault_settings
    if not config.addr or not config.token:
        raise VaultVerificationError("Vault address and token must be configured.")
    client = VaultTransitClient(
        base_url=config.addr,
        token=config.token,
        key_name=config.transit_key,
        namespace=config.namespace,
    )
    return VaultSecretProvider(client=client)


__all__ = ["VaultSecretProvider", "build_vault_secret_provider"]
