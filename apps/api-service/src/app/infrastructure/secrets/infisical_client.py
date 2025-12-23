"""Re-export shared Infisical API client."""

from starter_providers.secrets.infisical_client import InfisicalAPIClient, InfisicalAPIError

__all__ = ["InfisicalAPIClient", "InfisicalAPIError"]
