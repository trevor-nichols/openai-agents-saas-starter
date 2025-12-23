"""Re-export shared Azure Key Vault client."""

from starter_providers.secrets.azure_client import AzureKeyVaultClient, AzureKeyVaultError

__all__ = ["AzureKeyVaultClient", "AzureKeyVaultError"]
