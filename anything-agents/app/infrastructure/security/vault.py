"""Vault Transit client for request signature verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings


class VaultError(RuntimeError):
    """Base class for Vault-related exceptions."""


class VaultVerificationError(VaultError):
    """Raised when Transit verification fails or returns invalid response."""


class VaultClientUnavailable(VaultError):
    """Raised when Vault client cannot be initialized due to missing configuration."""


@dataclass
class VaultTransitClient:
    base_url: str
    token: str
    key_name: str
    timeout: float = 5.0

    def verify_signature(
        self, payload_b64: str, signature: str, transport: httpx.BaseTransport | None = None
    ) -> bool:
        """Verify a Vault Transit signature for the given payload."""

        url = f"{self.base_url.rstrip('/')}/v1/transit/verify/{self.key_name}"
        headers = {"X-Vault-Token": self.token}
        body = {"input": payload_b64, "signature": signature}

        with httpx.Client(timeout=self.timeout, transport=transport) as client:
            try:
                response = client.post(url, json=body, headers=headers)
            except httpx.HTTPError as exc:
                raise VaultVerificationError(f"Vault request failed: {exc}") from exc

        if response.status_code >= 400:
            raise VaultVerificationError(
                f"Vault verification request failed ({response.status_code}): {response.text}"
            )

        data: dict[str, Any] = response.json()
        valid = data.get("data", {}).get("valid")
        if valid is True:
            return True
        if valid is False:
            return False
        raise VaultVerificationError("Vault verification response missing 'valid' flag.")


def get_vault_transit_client() -> VaultTransitClient:
    settings = get_settings()

    if not settings.vault_addr or not settings.vault_token:
        raise VaultClientUnavailable("Vault address/token not configured.")

    return VaultTransitClient(
        base_url=settings.vault_addr,
        token=settings.vault_token,
        key_name=settings.vault_transit_key,
    )
