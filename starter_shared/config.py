"""Lightweight config bridge for the Agent Starter CLI.

This module exposes a narrow, import-safe surface that lets CLI code obtain the
backend's Pydantic settings without importing `anything-agents/app` directly at
module import time. The CLI should depend on the protocol defined here rather
than on the concrete FastAPI settings class.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import import_module
from typing import Any, Literal, Protocol, cast, runtime_checkable

from starter_shared.secrets.models import (
    AWSSecretsManagerConfig,
    AzureKeyVaultConfig,
    InfisicalProviderConfig,
    SecretsProviderLiteral,
    VaultProviderConfig,
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
    auth_key_storage_backend: str
    auth_key_storage_path: str
    auth_key_secret_name: str | None
    enable_billing: bool
    enable_billing_retry_worker: bool
    signup_access_policy: Literal["public", "invite_only", "approval"]
    allow_public_signup: bool
    signup_rate_limit_per_hour: int

    @property
    def vault_settings(self) -> VaultProviderConfig: ...

    @property
    def infisical_settings(self) -> InfisicalProviderConfig: ...

    @property
    def aws_settings(self) -> AWSSecretsManagerConfig: ...

    @property
    def azure_settings(self) -> AzureKeyVaultConfig: ...

    def secret_warnings(self) -> list[str]: ...

    def required_stripe_envs_missing(self) -> list[str]: ...


def _resolve_settings_class() -> type[StarterSettingsProtocol]:
    try:
        module = import_module("app.core.config")
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive
        raise RuntimeError("FastAPI settings module is unavailable") from exc
    settings_cls: Any = getattr(module, "Settings", None)
    if settings_cls is None:
        raise RuntimeError("app.core.config.Settings is missing")
    if not isinstance(settings_cls, type):
        raise RuntimeError("app.core.config.Settings is not a class")
    return cast(type[StarterSettingsProtocol], settings_cls)


@lru_cache(maxsize=1)
def get_settings() -> StarterSettingsProtocol:
    """Lazily instantiate (and cache) the FastAPI settings object."""

    settings_cls = _resolve_settings_class()
    settings = settings_cls()
    return cast(StarterSettingsProtocol, settings)


__all__ = ["StarterSettingsProtocol", "get_settings"]
