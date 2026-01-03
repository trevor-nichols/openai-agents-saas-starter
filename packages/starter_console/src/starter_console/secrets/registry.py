"""Lightweight registry mirroring backend secrets providers for CLI workflows."""

from __future__ import annotations

from dataclasses import dataclass

from starter_contracts.config import StarterSettingsProtocol
from starter_contracts.secrets.models import (
    AWSSecretsManagerConfig,
    AzureKeyVaultConfig,
    GCPSecretManagerConfig,
    InfisicalProviderConfig,
    SecretsProviderLiteral,
    VaultProviderConfig,
)


@dataclass(slots=True)
class CLISecretsProvider:
    """Simple descriptor returned to CLI commands."""

    kind: SecretsProviderLiteral
    vault: VaultProviderConfig | None = None
    infisical: InfisicalProviderConfig | None = None
    aws: AWSSecretsManagerConfig | None = None
    azure: AzureKeyVaultConfig | None = None
    gcp: GCPSecretManagerConfig | None = None


def resolve_cli_secrets_provider(settings: StarterSettingsProtocol) -> CLISecretsProvider:
    """
    Resolve the CLI's view of the configured secrets provider.

    Vault paths are supported today; Infisical implementations will land in later phases.
    """

    provider = settings.secrets_provider
    if provider in (SecretsProviderLiteral.VAULT_DEV, SecretsProviderLiteral.VAULT_HCP):
        return CLISecretsProvider(kind=provider, vault=settings.vault_settings)
    if provider in (
        SecretsProviderLiteral.INFISICAL_CLOUD,
        SecretsProviderLiteral.INFISICAL_SELF_HOST,
    ):
        return CLISecretsProvider(kind=provider, infisical=settings.infisical_settings)
    if provider is SecretsProviderLiteral.AWS_SM:
        return CLISecretsProvider(kind=provider, aws=settings.aws_settings)
    if provider is SecretsProviderLiteral.AZURE_KV:
        return CLISecretsProvider(kind=provider, azure=settings.azure_settings)
    if provider is SecretsProviderLiteral.GCP_SM:
        return CLISecretsProvider(kind=provider, gcp=settings.gcp_settings)

    raise RuntimeError(
        f"Secrets provider {provider.value} is not available in the CLI yet. "
        "Pick Vault until Infisical support lands."
    )
