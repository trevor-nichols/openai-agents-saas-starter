from __future__ import annotations

from starter_providers.secrets import (
    AWSSecretsManagerClient,
    AWSSecretsManagerError,
    AzureKeyVaultClient,
    AzureKeyVaultError,
    GCPSecretManagerClient,
    GCPSecretManagerError,
    InfisicalAPIClient,
    InfisicalAPIError,
)


def test_public_clients_importable() -> None:
    assert AWSSecretsManagerClient is not None
    assert AWSSecretsManagerError is not None
    assert AzureKeyVaultClient is not None
    assert AzureKeyVaultError is not None
    assert GCPSecretManagerClient is not None
    assert GCPSecretManagerError is not None
    assert InfisicalAPIClient is not None
    assert InfisicalAPIError is not None
