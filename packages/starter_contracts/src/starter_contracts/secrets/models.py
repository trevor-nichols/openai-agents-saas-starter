"""Shared secret-provider contracts used by both backend and CLI."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


class SecretsProviderLiteral(StrEnum):
    """Enumerates supported secrets providers."""

    VAULT_DEV = "vault_dev"
    VAULT_HCP = "vault_hcp"
    INFISICAL_CLOUD = "infisical_cloud"
    INFISICAL_SELF_HOST = "infisical_self_host"
    AWS_SM = "aws_sm"
    AZURE_KV = "azure_kv"
    GCP_SM = "gcp_sm"


class SecretScope(StrEnum):
    """Categorizes where or how a secret is consumed."""

    SERVICE_ACCOUNT = "service_account"
    DATABASE = "database"
    THIRD_PARTY_API = "third_party_api"
    INTERNAL = "internal"


class SecretPurpose(StrEnum):
    """Captures signing/verification intents."""

    SERVICE_ACCOUNT_ISSUANCE = "service_account_issuance"
    CLI_BRIDGE = "cli_bridge"
    GENERIC = "generic"


class SecretProviderStatus(StrEnum):
    """Health status states exposed by providers."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(slots=True)
class SignedPayload:
    """Normalized response from provider-specific signing operations."""

    signature: str
    algorithm: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SecretProviderHealth:
    """Surface provider readiness diagnostics."""

    status: SecretProviderStatus
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VaultProviderConfig:
    """Resolved Vault configuration shared between backend and CLI."""

    addr: str | None
    token: str | None
    transit_key: str
    namespace: str | None
    verify_enabled: bool


@dataclass(slots=True)
class InfisicalProviderConfig:
    """Resolved Infisical configuration shared across surfaces."""

    base_url: str | None
    service_token: str | None
    project_id: str | None
    environment: str | None
    secret_path: str | None
    ca_bundle_path: str | None
    signing_secret_name: str
    cache_ttl_seconds: int


@dataclass(slots=True)
class AWSSecretsManagerConfig:
    """Resolved AWS Secrets Manager configuration."""

    region: str
    signing_secret_arn: str
    profile: str | None
    access_key_id: str | None
    secret_access_key: str | None
    session_token: str | None
    cache_ttl_seconds: int


@dataclass(slots=True)
class AzureKeyVaultConfig:
    """Resolved Azure Key Vault configuration."""

    vault_url: str
    signing_secret_name: str
    tenant_id: str | None
    client_id: str | None
    client_secret: str | None
    managed_identity_client_id: str | None
    cache_ttl_seconds: int


@dataclass(slots=True)
class GCPSecretManagerConfig:
    """Resolved GCP Secret Manager configuration."""

    project_id: str
    signing_secret_name: str
    cache_ttl_seconds: int


@runtime_checkable
class SecretProviderProtocol(Protocol):
    """Async contract every secrets provider must satisfy."""

    async def get_secret(self, key: str, *, scope: SecretScope | None = None) -> str: ...

    async def get_secrets(
        self, keys: Sequence[str], *, scope: SecretScope | None = None
    ) -> dict[str, str]: ...

    async def sign(self, payload: bytes, *, purpose: SecretPurpose) -> SignedPayload: ...

    async def verify(
        self, payload: bytes, signature: str, *, purpose: SecretPurpose
    ) -> bool: ...

    async def health_check(self) -> SecretProviderHealth: ...


__all__ = [
    "AWSSecretsManagerConfig",
    "AzureKeyVaultConfig",
    "GCPSecretManagerConfig",
    "InfisicalProviderConfig",
    "SecretProviderHealth",
    "SecretProviderProtocol",
    "SecretProviderStatus",
    "SecretPurpose",
    "SecretScope",
    "SecretsProviderLiteral",
    "SignedPayload",
    "VaultProviderConfig",
]
