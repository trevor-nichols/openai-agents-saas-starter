"""Lightweight config bridge for the Agent Starter Console.

This module exposes a narrow, import-safe surface that lets CLI code obtain the
backend's Pydantic settings without importing `api-service/src/app` directly at
module import time. The CLI should depend on the protocol defined here rather
than on the concrete FastAPI settings class.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any, Literal, Protocol, cast, runtime_checkable

from starter_contracts.secrets.models import (
    AWSSecretsManagerConfig,
    AzureKeyVaultConfig,
    GCPSecretManagerConfig,
    InfisicalProviderConfig,
    SecretsProviderLiteral,
    VaultProviderConfig,
)
from starter_contracts.storage.models import (
    AzureBlobProviderConfig,
    GCSProviderConfig,
    MinioProviderConfig,
    S3ProviderConfig,
    StorageProviderLiteral,
)


@runtime_checkable
class StarterSettingsProtocol(Protocol):
    """Subset of settings fields/methods required by the CLI."""

    secrets_provider: SecretsProviderLiteral
    vault_addr: str | None
    vault_token: str | None
    vault_transit_key: str
    vault_namespace: str | None
    environment: str
    debug: bool
    vault_verify_enabled: bool
    infisical_base_url: str | None
    infisical_service_token: str | None
    infisical_project_id: str | None
    infisical_environment: str | None
    infisical_secret_path: str | None
    infisical_ca_bundle_path: str | None
    infisical_signing_secret_name: str
    infisical_cache_ttl_seconds: int
    aws_region: str | None
    aws_profile: str | None
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    aws_session_token: str | None
    aws_sm_signing_secret_arn: str | None
    aws_sm_cache_ttl_seconds: int
    azure_key_vault_url: str | None
    azure_kv_signing_secret_name: str | None
    azure_tenant_id: str | None
    azure_client_id: str | None
    azure_client_secret: str | None
    azure_managed_identity_client_id: str | None
    azure_kv_cache_ttl_seconds: int
    gcp_sm_project_id: str | None
    gcp_sm_signing_secret_name: str | None
    gcp_sm_cache_ttl_seconds: int
    auth_key_storage_backend: str
    auth_key_storage_provider: SecretsProviderLiteral | None
    auth_key_storage_path: str
    auth_key_secret_name: str | None
    enable_resend_email_delivery: bool
    resend_api_key: str | None
    resend_default_from: str | None
    enable_billing: bool
    enable_billing_retry_worker: bool
    openai_api_key: str | None
    signup_access_policy: Literal["public", "invite_only", "approval"]
    allow_public_signup: bool
    signup_rate_limit_per_hour: int
    storage_provider: StorageProviderLiteral
    storage_bucket_prefix: str | None
    storage_signed_url_ttl_seconds: int
    storage_max_file_mb: int
    storage_allowed_mime_types: list[str]
    minio_endpoint: str | None
    minio_access_key: str | None
    minio_secret_key: str | None
    minio_region: str | None
    minio_secure: bool
    gcs_project_id: str | None
    gcs_bucket: str | None
    gcs_credentials_json: str | None
    gcs_credentials_path: str | None
    gcs_signing_email: str | None
    gcs_uniform_access: bool
    s3_region: str | None
    s3_bucket: str | None
    s3_endpoint_url: str | None
    s3_force_path_style: bool
    azure_blob_account_url: str | None
    azure_blob_container: str | None
    azure_blob_connection_string: str | None

    @property
    def vault_settings(self) -> VaultProviderConfig: ...

    @property
    def infisical_settings(self) -> InfisicalProviderConfig: ...

    @property
    def aws_settings(self) -> AWSSecretsManagerConfig: ...

    @property
    def azure_settings(self) -> AzureKeyVaultConfig: ...

    @property
    def gcp_settings(self) -> GCPSecretManagerConfig: ...

    @property
    def minio_settings(self) -> MinioProviderConfig: ...

    @property
    def gcs_settings(self) -> GCSProviderConfig: ...

    @property
    def s3_settings(self) -> S3ProviderConfig: ...

    @property
    def azure_blob_settings(self) -> AzureBlobProviderConfig: ...

    def secret_warnings(self) -> list[str]: ...

    def required_stripe_envs_missing(self) -> list[str]: ...

    def should_enforce_secret_overrides(self) -> bool: ...


def _resolve_settings_class() -> type[StarterSettingsProtocol]:
    repo_root = Path(__file__).resolve().parents[4]
    api_src = repo_root / "apps" / "api-service" / "src"
    if api_src.is_dir():
        api_src_str = api_src.as_posix()
        if api_src_str not in sys.path:
            sys.path.insert(0, api_src_str)

    try:
        module = import_module("app.core.settings")
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive
        raise RuntimeError("FastAPI settings module is unavailable") from exc
    settings_cls: Any = getattr(module, "Settings", None)
    if settings_cls is None:
        raise RuntimeError("app.core.settings.Settings is missing")
    if not isinstance(settings_cls, type):
        raise RuntimeError("app.core.settings.Settings is not a class")
    return cast(type[StarterSettingsProtocol], settings_cls)


@lru_cache(maxsize=1)
def get_settings_class() -> type[StarterSettingsProtocol]:
    """Return the FastAPI Settings class without instantiating it.

    This is safe to call in tooling contexts (e.g., CLI schema inventory) where
    required environment variables may not be populated yet.
    """

    return _resolve_settings_class()


@lru_cache(maxsize=1)
def get_settings() -> StarterSettingsProtocol:
    """Lazily instantiate (and cache) the FastAPI settings object."""

    settings_cls = _resolve_settings_class()
    settings = settings_cls()
    return cast(StarterSettingsProtocol, settings)


__all__ = ["StarterSettingsProtocol", "get_settings", "get_settings_class"]
