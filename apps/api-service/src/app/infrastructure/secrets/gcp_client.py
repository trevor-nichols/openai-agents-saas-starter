"""Re-export shared GCP Secret Manager client."""

from starter_providers.secrets.gcp_client import (
    GCPSecretManagerClient,
    GCPSecretManagerError,
)

__all__ = ["GCPSecretManagerClient", "GCPSecretManagerError"]
