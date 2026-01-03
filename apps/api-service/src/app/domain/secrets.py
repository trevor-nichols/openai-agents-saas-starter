"""Backend-facing aliases for shared secret provider models."""

from starter_contracts.secrets.models import (
    AWSSecretsManagerConfig,
    AzureKeyVaultConfig,
    GCPSecretManagerConfig,
    InfisicalProviderConfig,
    SecretProviderHealth,
    SecretProviderProtocol,
    SecretProviderStatus,
    SecretPurpose,
    SecretScope,
    SecretsProviderLiteral,
    SignedPayload,
    VaultProviderConfig,
)

__all__ = [
    "InfisicalProviderConfig",
    "SecretProviderHealth",
    "SecretProviderProtocol",
    "SecretProviderStatus",
    "SecretPurpose",
    "SecretScope",
    "SecretsProviderLiteral",
    "SignedPayload",
    "VaultProviderConfig",
    "AWSSecretsManagerConfig",
    "AzureKeyVaultConfig",
    "GCPSecretManagerConfig",
]
