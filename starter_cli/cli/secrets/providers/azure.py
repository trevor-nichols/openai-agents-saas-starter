from __future__ import annotations

from azure.core.exceptions import AzureError
from azure.identity import (
    ChainedTokenCredential,
    ClientSecretCredential,
    DefaultAzureCredential,
    ManagedIdentityCredential,
)
from azure.keyvault.secrets import SecretClient
from starter_shared.secrets.models import SecretsProviderLiteral

from ...common import CLIContext
from ...console import console
from ...setup.inputs import InputProvider
from ..models import OnboardResult, SecretsWorkflowOptions


def run_azure_kv(
    ctx: CLIContext,
    provider: InputProvider,
    *,
    options: SecretsWorkflowOptions,
) -> OnboardResult:
    settings = ctx.optional_settings()
    defaults = settings.azure_settings if settings else None
    vault_url = provider.prompt_string(
        key="AZURE_KEY_VAULT_URL",
        prompt="Key Vault URL (https://<name>.vault.azure.net/)",
        default=defaults.vault_url if defaults and defaults.vault_url else None,
        required=True,
    )
    secret_name_default = (
        defaults.signing_secret_name if defaults and defaults.signing_secret_name else None
    )
    secret_name = provider.prompt_string(
        key="AZURE_KEY_VAULT_SECRET_NAME",
        prompt="Signing secret name",
        default=secret_name_default or "auth-signing-secret",
        required=True,
    )
    tenant_id = provider.prompt_string(
        key="AZURE_TENANT_ID",
        prompt="Tenant ID (optional)",
        default=defaults.tenant_id if defaults and defaults.tenant_id else "",
        required=False,
    )
    client_id = provider.prompt_string(
        key="AZURE_CLIENT_ID",
        prompt="Client ID (optional)",
        default=defaults.client_id if defaults and defaults.client_id else "",
        required=False,
    )
    client_secret = provider.prompt_secret(
        key="AZURE_CLIENT_SECRET",
        prompt="Client secret (optional)",
        existing=defaults.client_secret if defaults else None,
        required=False,
    )
    managed_identity_client_id = provider.prompt_string(
        key="AZURE_MANAGED_IDENTITY_CLIENT_ID",
        prompt="Managed identity client ID (optional)",
        default=(
            defaults.managed_identity_client_id
            if defaults and defaults.managed_identity_client_id
            else ""
        ),
        required=False,
    )

    verified = _probe_azure_secret(
        vault_url=vault_url,
        secret_name=secret_name,
        tenant_id=tenant_id or None,
        client_id=client_id or None,
        client_secret=client_secret or None,
        managed_identity_client_id=managed_identity_client_id or None,
    )

    env_updates = {
        "SECRETS_PROVIDER": SecretsProviderLiteral.AZURE_KV.value,
        "AZURE_KEY_VAULT_URL": vault_url,
        "AZURE_KEY_VAULT_SECRET_NAME": secret_name,
    }
    if tenant_id:
        env_updates["AZURE_TENANT_ID"] = tenant_id
    if client_id:
        env_updates["AZURE_CLIENT_ID"] = client_id
    if client_secret:
        env_updates["AZURE_CLIENT_SECRET"] = client_secret
    if managed_identity_client_id:
        env_updates["AZURE_MANAGED_IDENTITY_CLIENT_ID"] = managed_identity_client_id

    steps = [
        (
            "Assign the Key Vault Secrets User role (or equivalent) to the service principal or "
            "managed identity."
        ),
        "Ensure the signing secret exists in Key Vault; rotate by updating the secret value.",
        "Add the env vars above to backend + CLI and restart FastAPI.",
    ]
    warnings: list[str] = []
    if verified:
        steps.insert(0, "Validated Key Vault access by reading the signing secret.")
    else:
        warnings.append(
            "Azure Key Vault validation failed. Check tenant/app credentials "
            "or managed identity permissions."
        )

    return OnboardResult(
        provider=SecretsProviderLiteral.AZURE_KV,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
    )


def _probe_azure_secret(
    *,
    vault_url: str,
    secret_name: str,
    tenant_id: str | None,
    client_id: str | None,
    client_secret: str | None,
    managed_identity_client_id: str | None,
) -> bool:
    try:
        credentials = []
        if tenant_id and client_id and client_secret:
            credentials.append(
                ClientSecretCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret,
                )
            )
        if managed_identity_client_id:
            credentials.append(
                ManagedIdentityCredential(client_id=managed_identity_client_id)
            )
        credentials.append(
            DefaultAzureCredential(exclude_interactive_browser_credential=True)
        )
        credential = (
            credentials[0]
            if len(credentials) == 1
            else ChainedTokenCredential(*credentials)
        )
        client = SecretClient(vault_url=vault_url, credential=credential)
        client.get_secret(secret_name)
        return True
    except AzureError as exc:  # pragma: no cover - external dependency
        console.warn(f"Azure probe failed: {exc}", topic="secrets")
        return False


__all__ = ["run_azure_kv"]
