"""Register the secret-manager client used for key storage."""

from __future__ import annotations

import logging

from starter_contracts.keys import (
    KeyStorageError,
    SecretManagerClient,
    register_secret_manager_client,
    resolve_key_storage_provider,
)

from app.core.settings import Settings
from app.domain.secrets import SecretsProviderLiteral
from app.infrastructure.secrets.aws_client import AWSSecretsManagerClient, AWSSecretsManagerError
from app.infrastructure.secrets.azure_client import AzureKeyVaultClient, AzureKeyVaultError
from app.infrastructure.secrets.gcp_client import GCPSecretManagerClient, GCPSecretManagerError
from app.infrastructure.secrets.infisical_client import InfisicalAPIClient, InfisicalAPIError
from app.infrastructure.security.vault_kv import configure_vault_secret_manager

logger = logging.getLogger(__name__)


class AWSSecretManagerKeyStorageClient(SecretManagerClient):
    def __init__(self, settings: Settings) -> None:
        config = settings.aws_settings
        if not config.region:
            raise KeyStorageError("AWS_REGION must be set for secret-manager key storage.")
        self._client = AWSSecretsManagerClient(
            region=config.region,
            profile=config.profile,
            access_key_id=config.access_key_id,
            secret_access_key=config.secret_access_key,
            session_token=config.session_token,
        )

    def read_secret(self, name: str) -> str | None:
        try:
            return self._client.get_secret_value_optional(name)
        except AWSSecretsManagerError as exc:
            raise KeyStorageError(str(exc)) from exc

    def write_secret(self, name: str, value: str) -> None:
        try:
            self._client.put_secret_value(name, value)
        except AWSSecretsManagerError as exc:
            raise KeyStorageError(str(exc)) from exc


class AzureKeyVaultSecretManagerClient(SecretManagerClient):
    def __init__(self, settings: Settings) -> None:
        config = settings.azure_settings
        if not config.vault_url:
            raise KeyStorageError("AZURE_KEY_VAULT_URL must be set for secret-manager key storage.")
        self._client = AzureKeyVaultClient(
            vault_url=config.vault_url,
            tenant_id=config.tenant_id,
            client_id=config.client_id,
            client_secret=config.client_secret,
            managed_identity_client_id=config.managed_identity_client_id,
        )

    def read_secret(self, name: str) -> str | None:
        try:
            return self._client.get_secret_optional(name)
        except AzureKeyVaultError as exc:
            raise KeyStorageError(str(exc)) from exc

    def write_secret(self, name: str, value: str) -> None:
        try:
            self._client.set_secret(name, value)
        except AzureKeyVaultError as exc:
            raise KeyStorageError(str(exc)) from exc


class InfisicalSecretManagerKeyStorageClient(SecretManagerClient):
    def __init__(self, settings: Settings) -> None:
        config = settings.infisical_settings
        if not (
            config.base_url
            and config.service_token
            and config.project_id
            and config.environment
        ):
            raise KeyStorageError(
                "INFISICAL_BASE_URL, INFISICAL_SERVICE_TOKEN, INFISICAL_PROJECT_ID, and "
                "INFISICAL_ENVIRONMENT must be set for secret-manager key storage."
            )
        self._client = InfisicalAPIClient(
            base_url=config.base_url,
            service_token=config.service_token,
            project_id=config.project_id,
            environment=config.environment,
            secret_path=config.secret_path or "/",
            ca_bundle_path=config.ca_bundle_path,
        )

    def read_secret(self, name: str) -> str | None:
        try:
            return self._client.get_secret(name)
        except InfisicalAPIError as exc:
            raise KeyStorageError(str(exc)) from exc

    def write_secret(self, name: str, value: str) -> None:
        try:
            self._client.set_secret(name, value)
        except InfisicalAPIError as exc:
            raise KeyStorageError(str(exc)) from exc


class GCPSecretManagerKeyStorageClient(SecretManagerClient):
    def __init__(self, settings: Settings) -> None:
        config = settings.gcp_settings
        secret_name = settings.auth_key_secret_name or ""
        if not config.project_id and not secret_name.startswith("projects/"):
            raise KeyStorageError(
                "GCP_SM_PROJECT_ID or GCP_PROJECT_ID must be set when "
                "auth_key_secret_name is not fully qualified."
            )
        try:
            self._client = GCPSecretManagerClient(project_id=config.project_id or None)
        except GCPSecretManagerError as exc:
            raise KeyStorageError(str(exc)) from exc

    def read_secret(self, name: str) -> str | None:
        try:
            return self._client.get_secret_value_optional(name)
        except GCPSecretManagerError as exc:
            raise KeyStorageError(str(exc)) from exc

    def write_secret(self, name: str, value: str) -> None:
        try:
            self._client.put_secret_value(name, value)
        except GCPSecretManagerError as exc:
            raise KeyStorageError(str(exc)) from exc


def configure_secret_manager_client(settings: Settings) -> None:
    """Register a SecretManagerClient for keyset storage based on AUTH_KEY_STORAGE_PROVIDER."""

    if settings.auth_key_storage_backend != "secret-manager":
        return

    provider = resolve_key_storage_provider(settings)
    if provider in {SecretsProviderLiteral.VAULT_DEV, SecretsProviderLiteral.VAULT_HCP}:
        configure_vault_secret_manager(settings)
        return

    if provider == SecretsProviderLiteral.AWS_SM:
        register_secret_manager_client(lambda: AWSSecretManagerKeyStorageClient(settings))
        logger.info("Registered AWS Secrets Manager key storage client.")
        return

    if provider == SecretsProviderLiteral.AZURE_KV:
        register_secret_manager_client(lambda: AzureKeyVaultSecretManagerClient(settings))
        logger.info("Registered Azure Key Vault key storage client.")
        return

    if provider == SecretsProviderLiteral.GCP_SM:
        register_secret_manager_client(lambda: GCPSecretManagerKeyStorageClient(settings))
        logger.info("Registered GCP Secret Manager key storage client.")
        return

    if provider in {
        SecretsProviderLiteral.INFISICAL_CLOUD,
        SecretsProviderLiteral.INFISICAL_SELF_HOST,
    }:
        register_secret_manager_client(lambda: InfisicalSecretManagerKeyStorageClient(settings))
        logger.info("Registered Infisical key storage client.")
        return

    raise KeyStorageError(
        "Secret-manager key storage is only supported for Vault, Infisical, AWS Secrets Manager, "
        f"Azure Key Vault, or GCP Secret Manager (current provider: {provider.value})."
    )


__all__ = ["configure_secret_manager_client"]
