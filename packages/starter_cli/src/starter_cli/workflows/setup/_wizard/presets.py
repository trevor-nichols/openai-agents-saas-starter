from __future__ import annotations

from starter_contracts.secrets.models import SecretsProviderLiteral
from starter_contracts.storage.models import StorageProviderLiteral

from .context import WizardContext


def apply_hosting_preset(context: WizardContext) -> None:
    preset = context.hosting_preset
    if not preset:
        return

    if preset == "local_docker":
        _apply_local_defaults(context)
        return
    if preset == "cloud_managed":
        _apply_cloud_defaults(context)
        return


def _apply_local_defaults(context: WizardContext) -> None:
    context.set_backend_default("STARTER_LOCAL_DATABASE_MODE", "compose")
    context.set_backend_default("REDIS_URL", "redis://localhost:6379/0")
    context.set_backend_default("SECRETS_PROVIDER", SecretsProviderLiteral.VAULT_DEV.value)
    context.set_backend_default("STORAGE_PROVIDER", StorageProviderLiteral.MINIO.value)
    context.set_backend_bool_default("ENABLE_BILLING", False)


def _apply_cloud_defaults(context: WizardContext) -> None:
    context.set_backend_default("STARTER_LOCAL_DATABASE_MODE", "external")
    provider = (context.cloud_provider or "").strip().lower()
    if provider == "azure":
        context.set_backend_default("SECRETS_PROVIDER", SecretsProviderLiteral.AZURE_KV.value)
        context.set_backend_default("STORAGE_PROVIDER", StorageProviderLiteral.AZURE_BLOB.value)
    elif provider == "gcp":
        context.set_backend_default(
            "SECRETS_PROVIDER", SecretsProviderLiteral.INFISICAL_CLOUD.value
        )
        context.set_backend_default("STORAGE_PROVIDER", StorageProviderLiteral.GCS.value)
    else:  # aws or other default
        context.set_backend_default("SECRETS_PROVIDER", SecretsProviderLiteral.AWS_SM.value)
        context.set_backend_default("STORAGE_PROVIDER", StorageProviderLiteral.S3.value)

    context.set_backend_bool_default("ENABLE_BILLING", True)


__all__ = ["apply_hosting_preset"]
