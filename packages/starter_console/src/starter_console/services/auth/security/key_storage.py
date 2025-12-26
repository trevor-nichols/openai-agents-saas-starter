"""Configure key storage secret-manager clients for the CLI."""

from __future__ import annotations

from starter_contracts.keys import (
    KeyStorageError,
    SecretManagerClient,
    register_secret_manager_client,
    resolve_key_storage_provider,
)
from starter_contracts.secrets.models import SecretsProviderLiteral
from starter_contracts.vault_kv import configure_vault_secret_manager
from starter_providers.secrets import (
    AWSSecretsManagerClient,
    AWSSecretsManagerError,
    AzureKeyVaultClient,
    AzureKeyVaultError,
)
from starter_providers.secrets.infisical_client import InfisicalAPIClient, InfisicalAPIError

from starter_console.core import CLIContext


class AWSSecretManagerKeyStorageClient(SecretManagerClient):
    def __init__(self, ctx: CLIContext) -> None:
        settings = ctx.require_settings()
        aws = settings.aws_settings
        if not aws.region:
            raise KeyStorageError("AWS_REGION must be set for key storage.")
        self._client = AWSSecretsManagerClient(
            region=aws.region,
            profile=aws.profile,
            access_key_id=aws.access_key_id,
            secret_access_key=aws.secret_access_key,
            session_token=aws.session_token,
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
    def __init__(self, ctx: CLIContext) -> None:
        settings = ctx.require_settings()
        azure = settings.azure_settings
        if not azure.vault_url:
            raise KeyStorageError("AZURE_KEY_VAULT_URL must be set for key storage.")
        self._client = AzureKeyVaultClient(
            vault_url=azure.vault_url,
            tenant_id=azure.tenant_id,
            client_id=azure.client_id,
            client_secret=azure.client_secret,
            managed_identity_client_id=azure.managed_identity_client_id,
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
    def __init__(self, ctx: CLIContext) -> None:
        settings = ctx.require_settings()
        config = settings.infisical_settings
        if not (
            config.base_url
            and config.service_token
            and config.project_id
            and config.environment
        ):
            raise KeyStorageError(
                "INFISICAL_BASE_URL, INFISICAL_SERVICE_TOKEN, INFISICAL_PROJECT_ID, and "
                "INFISICAL_ENVIRONMENT must be set for key storage."
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


def configure_key_storage_secret_manager(ctx: CLIContext) -> None:
    settings = ctx.require_settings()
    if settings.auth_key_storage_backend != "secret-manager":
        return

    provider = resolve_key_storage_provider(settings)
    if provider in {SecretsProviderLiteral.VAULT_DEV, SecretsProviderLiteral.VAULT_HCP}:
        configure_vault_secret_manager(settings)
        return

    if provider == SecretsProviderLiteral.AWS_SM:
        register_secret_manager_client(lambda: AWSSecretManagerKeyStorageClient(ctx))
        return

    if provider == SecretsProviderLiteral.AZURE_KV:
        register_secret_manager_client(lambda: AzureKeyVaultSecretManagerClient(ctx))
        return

    if provider in {
        SecretsProviderLiteral.INFISICAL_CLOUD,
        SecretsProviderLiteral.INFISICAL_SELF_HOST,
    }:
        register_secret_manager_client(lambda: InfisicalSecretManagerKeyStorageClient(ctx))
        return

    raise KeyStorageError(f"Unsupported key storage provider: {provider.value}")


__all__ = ["configure_key_storage_secret_manager"]
