from __future__ import annotations

from starter_providers.secrets import (
    AWSSecretsManagerClient,
    AWSSecretsManagerError,
    AzureKeyVaultClient,
    AzureKeyVaultError,
    InfisicalAPIClient,
    InfisicalAPIError,
)


def test_public_clients_importable() -> None:
    assert AWSSecretsManagerClient
    assert AWSSecretsManagerError
    assert AzureKeyVaultClient
    assert AzureKeyVaultError
    assert InfisicalAPIClient
    assert InfisicalAPIError
