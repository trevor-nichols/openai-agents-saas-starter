"""Azure Key Vault client helper."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.identity import (
    ChainedTokenCredential,
    ClientSecretCredential,
    DefaultAzureCredential,
    ManagedIdentityCredential,
)
from azure.keyvault.secrets import SecretClient


class AzureKeyVaultError(RuntimeError):
    """Raised when Azure Key Vault operations fail."""


@dataclass(slots=True)
class AzureKeyVaultClient:
    vault_url: str
    tenant_id: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    managed_identity_client_id: str | None = None
    _client: SecretClient = field(init=False, repr=False)

    def __post_init__(self) -> None:
        credentials: list[Any] = []
        if self.tenant_id and self.client_id and self.client_secret:
            credentials.append(
                ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )
            )
        if self.managed_identity_client_id:
            credentials.append(
                ManagedIdentityCredential(client_id=self.managed_identity_client_id)
            )

        credentials.append(
            DefaultAzureCredential(exclude_interactive_browser_credential=True)
        )

        if len(credentials) == 1:
            credential = credentials[0]
        else:
            credential = ChainedTokenCredential(*credentials)

        self._client = SecretClient(vault_url=self.vault_url, credential=credential)

    def get_secret(self, name: str) -> str:
        value = self.get_secret_optional(name)
        if value is None:
            raise AzureKeyVaultError(f"Secret {name} was not found.")
        return value

    def get_secret_optional(self, name: str) -> str | None:
        try:
            secret = self._client.get_secret(name)
        except ResourceNotFoundError:
            return None
        except AzureError as exc:  # pragma: no cover - network code
            raise AzureKeyVaultError(f"Failed to read secret {name}: {exc}") from exc
        if secret.value is None:
            raise AzureKeyVaultError(f"Secret {name} has no value.")
        return secret.value

    def set_secret(self, name: str, value: str) -> None:
        try:
            self._client.set_secret(name, value)
        except AzureError as exc:  # pragma: no cover - network code
            raise AzureKeyVaultError(f"Failed to write secret {name}: {exc}") from exc

    def ping(self, name: str) -> None:
        self.get_secret(name)


__all__ = ["AzureKeyVaultClient", "AzureKeyVaultError"]
