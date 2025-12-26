"""Re-export shared AWS Secrets Manager client."""

from starter_providers.secrets.aws_client import AWSSecretsManagerClient, AWSSecretsManagerError

__all__ = ["AWSSecretsManagerClient", "AWSSecretsManagerError"]
