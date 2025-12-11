"""Secrets provider integrations and Vault verification toggles."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.secrets import (
    AWSSecretsManagerConfig,
    AzureKeyVaultConfig,
    InfisicalProviderConfig,
    SecretsProviderLiteral,
    VaultProviderConfig,
)

from .base import VAULT_PROVIDER_KEYS


class SecretsProviderSettingsMixin(BaseModel):
    secrets_provider: SecretsProviderLiteral = Field(
        default=SecretsProviderLiteral.VAULT_DEV,
        description=(
            "Which secrets provider implementation to use (vault_dev, vault_hcp, "
            "infisical_cloud, infisical_self_host, aws_sm, azure_kv)."
        ),
        alias="SECRETS_PROVIDER",
    )
    vault_addr: str | None = Field(
        default=None,
        description="HashiCorp Vault address for Transit verification.",
        alias="VAULT_ADDR",
    )
    vault_token: str | None = Field(
        default=None,
        description="Vault token/AppRole secret with transit:verify capability.",
        alias="VAULT_TOKEN",
    )
    vault_transit_key: str = Field(
        default="auth-service",
        description="Transit key name used for signing/verification.",
        alias="VAULT_TRANSIT_KEY",
    )
    vault_namespace: str | None = Field(
        default=None,
        description="Optional Vault namespace for HCP or multi-tenant clusters.",
        alias="VAULT_NAMESPACE",
    )
    vault_verify_enabled: bool = Field(
        default=False,
        description="When true, enforce Vault Transit verification for service-account issuance.",
        alias="VAULT_VERIFY_ENABLED",
    )
    infisical_base_url: str | None = Field(
        default=None,
        description="Base URL for Infisical API (set when using Infisical providers).",
        alias="INFISICAL_BASE_URL",
    )
    infisical_service_token: str | None = Field(
        default=None,
        description="Infisical service token used for non-interactive secret access.",
        alias="INFISICAL_SERVICE_TOKEN",
    )
    infisical_project_id: str | None = Field(
        default=None,
        description="Infisical project identifier associated with this deployment.",
        alias="INFISICAL_PROJECT_ID",
    )
    infisical_environment: str | None = Field(
        default=None,
        description="Infisical environment slug (e.g., dev, staging, prod).",
        alias="INFISICAL_ENVIRONMENT",
    )
    infisical_secret_path: str | None = Field(
        default=None,
        description="Secret path (e.g., /backend) to read when seeding env vars.",
        alias="INFISICAL_SECRET_PATH",
    )
    infisical_ca_bundle_path: str | None = Field(
        default=None,
        description="Optional CA bundle path for self-hosted Infisical instances.",
        alias="INFISICAL_CA_BUNDLE_PATH",
    )
    infisical_signing_secret_name: str = Field(
        default="auth-service-signing-secret",
        description=(
            "Infisical secret name holding the shared signing key for service-account payloads."
        ),
        alias="INFISICAL_SIGNING_SECRET_NAME",
    )
    infisical_cache_ttl_seconds: int = Field(
        default=60,
        description="TTL (seconds) for Infisical secret cache entries.",
        alias="INFISICAL_CACHE_TTL_SECONDS",
    )
    aws_region: str | None = Field(
        default=None,
        description="AWS region for Secrets Manager requests.",
        alias="AWS_REGION",
    )
    aws_profile: str | None = Field(
        default=None,
        description="Named AWS profile to use when loading credentials.",
        alias="AWS_PROFILE",
    )
    aws_access_key_id: str | None = Field(
        default=None,
        description="AWS access key ID (overrides profile/IMDS when set).",
        alias="AWS_ACCESS_KEY_ID",
    )
    aws_secret_access_key: str | None = Field(
        default=None,
        description="AWS secret access key.",
        alias="AWS_SECRET_ACCESS_KEY",
    )
    aws_session_token: str | None = Field(
        default=None,
        description="AWS session token (for temporary credentials).",
        alias="AWS_SESSION_TOKEN",
    )
    aws_sm_signing_secret_arn: str | None = Field(
        default=None,
        description="Secrets Manager ARN/name containing the signing secret value.",
        alias="AWS_SM_SIGNING_SECRET_ARN",
    )
    aws_sm_cache_ttl_seconds: int = Field(
        default=60,
        description="TTL (seconds) for cached Secrets Manager values.",
        alias="AWS_SM_CACHE_TTL_SECONDS",
    )
    azure_key_vault_url: str | None = Field(
        default=None,
        description="Azure Key Vault URL (https://<name>.vault.azure.net).",
        alias="AZURE_KEY_VAULT_URL",
    )
    azure_kv_signing_secret_name: str | None = Field(
        default=None,
        description="Key Vault secret name containing the signing secret value.",
        alias="AZURE_KV_SIGNING_SECRET_NAME",
    )
    azure_tenant_id: str | None = Field(
        default=None,
        description="Azure AD tenant ID for service principal auth.",
        alias="AZURE_TENANT_ID",
    )
    azure_client_id: str | None = Field(
        default=None,
        description="Azure AD application (client) ID.",
        alias="AZURE_CLIENT_ID",
    )
    azure_client_secret: str | None = Field(
        default=None,
        description="Azure AD application secret.",
        alias="AZURE_CLIENT_SECRET",
    )
    azure_managed_identity_client_id: str | None = Field(
        default=None,
        description="User-assigned managed identity client ID (optional).",
        alias="AZURE_MANAGED_IDENTITY_CLIENT_ID",
    )
    azure_kv_cache_ttl_seconds: int = Field(
        default=60,
        description="TTL (seconds) for cached Key Vault secret values.",
        alias="AZURE_KV_CACHE_TTL_SECONDS",
    )
    enable_secrets_provider_telemetry: bool = Field(
        default=False,
        description="Emit structured metrics/logs about secrets provider selection (no payloads).",
        alias="ENABLE_SECRETS_PROVIDER_TELEMETRY",
    )

    @property
    def vault_settings(self) -> VaultProviderConfig:
        return VaultProviderConfig(
            addr=self.vault_addr,
            token=self.vault_token,
            transit_key=self.vault_transit_key,
            namespace=self.vault_namespace,
            verify_enabled=self.vault_verify_enabled,
        )

    @property
    def infisical_settings(self) -> InfisicalProviderConfig:
        return InfisicalProviderConfig(
            base_url=self.infisical_base_url,
            service_token=self.infisical_service_token,
            project_id=self.infisical_project_id,
            environment=self.infisical_environment,
            secret_path=self.infisical_secret_path,
            ca_bundle_path=self.infisical_ca_bundle_path,
            signing_secret_name=self.infisical_signing_secret_name,
            cache_ttl_seconds=self.infisical_cache_ttl_seconds,
        )

    @property
    def aws_settings(self) -> AWSSecretsManagerConfig:
        return AWSSecretsManagerConfig(
            region=self.aws_region or "",
            signing_secret_arn=self.aws_sm_signing_secret_arn or "",
            profile=self.aws_profile,
            access_key_id=self.aws_access_key_id,
            secret_access_key=self.aws_secret_access_key,
            session_token=self.aws_session_token,
            cache_ttl_seconds=self.aws_sm_cache_ttl_seconds,
        )

    @property
    def azure_settings(self) -> AzureKeyVaultConfig:
        return AzureKeyVaultConfig(
            vault_url=self.azure_key_vault_url or "",
            signing_secret_name=self.azure_kv_signing_secret_name or "",
            tenant_id=self.azure_tenant_id,
            client_id=self.azure_client_id,
            client_secret=self.azure_client_secret,
            managed_identity_client_id=self.azure_managed_identity_client_id,
            cache_ttl_seconds=self.azure_kv_cache_ttl_seconds,
        )

    def should_require_vault_verification(self) -> bool:
        guard = getattr(self, "should_enforce_secret_overrides", None)
        if callable(guard):
            return bool(self.vault_verify_enabled or guard())
        return bool(self.vault_verify_enabled)

    def vault_requirements_missing(self) -> list[str]:
        if self.secrets_provider not in VAULT_PROVIDER_KEYS:
            return []
        missing: list[str] = []
        if not self.vault_addr:
            missing.append("VAULT_ADDR")
        if not self.vault_token:
            missing.append("VAULT_TOKEN")
        if not self.vault_transit_key:
            missing.append("VAULT_TRANSIT_KEY")
        return missing
