"""Vault KV-backed secret manager client for key storage."""

from __future__ import annotations

import json

import httpx

from starter_shared.config import StarterSettingsProtocol, get_settings
from starter_shared.keys import KeyStorageError, SecretManagerClient, register_secret_manager_client


class VaultKVSecretManagerClient(SecretManagerClient):
    """Reads/writes secrets from HashiCorp Vault KV (v2-compatible)."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._transport = transport

    def read_secret(self, name: str) -> str | None:
        url = self._build_url(name)
        headers = self._headers()

        with httpx.Client(timeout=self.timeout, transport=self._transport) as client:
            response = client.get(url, headers=headers)

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise KeyStorageError(f"Vault KV read failed ({response.status_code}): {response.text}")

        payload = response.json()
        data = payload.get("data", {})
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        value = data.get("value")
        if value is None:
            raise KeyStorageError("Vault KV secret missing 'value' field.")
        if isinstance(value, str):
            return value
        return json.dumps(value)

    def write_secret(self, name: str, value: str) -> None:
        url = self._build_url(name)
        headers = self._headers()
        body = {"data": {"value": value}}

        with httpx.Client(timeout=self.timeout, transport=self._transport) as client:
            response = client.post(url, headers=headers, json=body)

        if response.status_code >= 400:
            raise KeyStorageError(
                f"Vault KV write failed ({response.status_code}): {response.text}"
            )

    def _build_url(self, name: str) -> str:
        path = name.lstrip("/")
        return f"{self.base_url}/v1/{path}"

    def _headers(self) -> dict[str, str]:
        return {"X-Vault-Token": self.token}


def configure_vault_secret_manager(settings: StarterSettingsProtocol | None = None) -> None:
    """
    Register the Vault KV secret manager client when backend=secret-manager.

    Safe to call multiple times; registration only occurs when configuration demands it.
    """

    settings = settings or get_settings()
    if settings.auth_key_storage_backend != "secret-manager":
        return

    vault_addr = settings.vault_addr
    vault_token = settings.vault_token

    if not vault_addr or not vault_token:
        raise KeyStorageError(
            "Vault address/token are required when auth_key_storage_backend=secret-manager."
        )
    if not settings.auth_key_secret_name:
        raise KeyStorageError("auth_key_secret_name must be configured for secret-manager backend.")

    def factory() -> VaultKVSecretManagerClient:
        return VaultKVSecretManagerClient(
            base_url=vault_addr,
            token=vault_token,
        )

    register_secret_manager_client(factory)
