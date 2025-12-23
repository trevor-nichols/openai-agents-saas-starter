from __future__ import annotations

import argparse

from starter_contracts.secrets.models import SecretsProviderLiteral

from starter_cli.commands.auth import handle_keys_rotate
from starter_cli.core import CLIError
from starter_cli.workflows.secrets import registry

from ...automation import AutomationPhase, AutomationStatus
from ...inputs import InputProvider, is_headless_provider
from ...validators import probe_vault_transit
from ..context import WizardContext

_VAULT_PROVIDERS = {
    SecretsProviderLiteral.VAULT_DEV,
    SecretsProviderLiteral.VAULT_HCP,
}


def run(context: WizardContext, provider: InputProvider) -> None:
    context.console.section(
        "Secrets & Vault",
        "Generate peppers, provision signing keys, and choose a secrets provider.",
    )
    _collect_secrets(context, provider)
    selected_provider = _collect_provider_choice(context, provider)
    context.set_backend("SECRETS_PROVIDER", selected_provider.value)
    if selected_provider not in _VAULT_PROVIDERS:
        _force_verification_flag(context)

    telemetry = provider.prompt_bool(
        key="ENABLE_SECRETS_PROVIDER_TELEMETRY",
        prompt="Opt into secrets-provider telemetry?",
        default=context.current_bool("ENABLE_SECRETS_PROVIDER_TELEMETRY", False),
    )
    context.set_backend_bool("ENABLE_SECRETS_PROVIDER_TELEMETRY", telemetry)

    rotate = provider.prompt_bool(
        key="ROTATE_SIGNING_KEYS",
        prompt="Rotate the Ed25519 signing keyset now?",
        default=False,
    )
    if rotate:
        _rotate_signing_keys(context)

    _run_provider_workflow(context, provider, selected_provider)
    _collect_key_storage_provider(context, provider, selected_provider)


def _collect_secrets(context: WizardContext, provider: InputProvider) -> None:
    context.ensure_secret(provider, key="SECRET_KEY", label="Application SECRET_KEY")
    context.ensure_secret(provider, key="AUTH_PASSWORD_PEPPER", label="Password hashing pepper")
    context.ensure_secret(provider, key="AUTH_REFRESH_TOKEN_PEPPER", label="Refresh token pepper")
    context.ensure_secret(
        provider,
        key="AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER",
        label="Email verification token pepper",
    )
    context.ensure_secret(
        provider,
        key="AUTH_PASSWORD_RESET_TOKEN_PEPPER",
        label="Password reset token pepper",
    )
    context.ensure_secret(
        provider,
        key="AUTH_SESSION_ENCRYPTION_KEY",
        label="Session encryption key",
        length=64,
    )
    salt_default = context.current("AUTH_SESSION_IP_HASH_SALT") or ""
    salt_value = provider.prompt_string(
        key="AUTH_SESSION_IP_HASH_SALT",
        prompt="Session IP hash salt (optional)",
        default=salt_default,
        required=False,
    )
    if salt_value:
        context.set_backend("AUTH_SESSION_IP_HASH_SALT", salt_value)


def _collect_provider_choice(
    context: WizardContext,
    provider: InputProvider,
) -> SecretsProviderLiteral:
    default_provider = context.current("SECRETS_PROVIDER") or SecretsProviderLiteral.VAULT_DEV.value
    while True:
        choice = (
            provider.prompt_string(
                key="SECRETS_PROVIDER",
                prompt=(
                    "Secrets provider "
                    "(vault_dev/vault_hcp/infisical_cloud/infisical_self_host/aws_sm/azure_kv)"
                ),
                default=default_provider,
                required=True,
            )
            .strip()
            .lower()
        )
        try:
            return SecretsProviderLiteral(choice)
        except ValueError:
            if is_headless_provider(provider):
                raise CLIError(f"Invalid secrets provider '{choice}'.") from None
            context.console.warn(
                "Invalid secrets provider. Please choose a supported value.",
                topic="secrets",
            )


def _run_provider_workflow(
    context: WizardContext,
    provider: InputProvider,
    literal: SecretsProviderLiteral,
) -> None:
    if literal in _VAULT_PROVIDERS:
        enable_vault = _collect_vault(context, provider)
        if literal == SecretsProviderLiteral.VAULT_HCP:
            namespace = provider.prompt_string(
                key="VAULT_NAMESPACE",
                prompt="Vault namespace (optional)",
                default=context.current("VAULT_NAMESPACE") or "",
                required=False,
            )
            if namespace:
                context.set_backend("VAULT_NAMESPACE", namespace)
        _ensure_vault_infra(context, enable_vault)
        if enable_vault:
            _verify_vault_transit(context)
        return

    from starter_cli.workflows.secrets.models import SecretsWorkflowOptions

    runner = registry.get_runner(literal)
    result = runner(
        context.cli_ctx,
        provider,
        options=SecretsWorkflowOptions(skip_automation=True),
    )
    for key, value in result.env_updates.items():
        context.set_backend(key, value)


def _collect_key_storage_provider(
    context: WizardContext,
    provider: InputProvider,
    selected_provider: SecretsProviderLiteral,
) -> None:
    backend = context.current("AUTH_KEY_STORAGE_BACKEND")
    if backend != "secret-manager":
        return

    current = context.current("AUTH_KEY_STORAGE_PROVIDER") or selected_provider.value
    try:
        key_provider = SecretsProviderLiteral(current)
    except ValueError as exc:
        raise CLIError(f"Invalid AUTH_KEY_STORAGE_PROVIDER '{current}'.") from exc

    context.set_backend("AUTH_KEY_STORAGE_PROVIDER", key_provider.value)
    if key_provider == selected_provider:
        return

    context.console.section(
        "Key Storage Provider",
        "Capture credentials for the key storage provider (distinct from SECRETS_PROVIDER).",
    )

    if key_provider in {SecretsProviderLiteral.VAULT_DEV, SecretsProviderLiteral.VAULT_HCP}:
        _collect_vault_kv(context, provider)
        return
    if key_provider == SecretsProviderLiteral.AWS_SM:
        _collect_aws_key_storage(context, provider)
        return
    if key_provider == SecretsProviderLiteral.AZURE_KV:
        _collect_azure_key_storage(context, provider)
        return
    if key_provider in {
        SecretsProviderLiteral.INFISICAL_CLOUD,
        SecretsProviderLiteral.INFISICAL_SELF_HOST,
    }:
        _collect_infisical_key_storage(context, provider, key_provider)
        return

    raise CLIError(f"Unsupported key storage provider '{key_provider.value}'.")


def _collect_vault_kv(context: WizardContext, provider: InputProvider) -> None:
    addr = provider.prompt_string(
        key="VAULT_ADDR",
        prompt="Vault address",
        default=context.current("VAULT_ADDR") or "https://vault.example.com",
        required=True,
    )
    token = provider.prompt_secret(
        key="VAULT_TOKEN",
        prompt="Vault token/AppRole secret",
        existing=context.current("VAULT_TOKEN"),
        required=True,
    )
    namespace = provider.prompt_string(
        key="VAULT_NAMESPACE",
        prompt="Vault namespace (optional)",
        default=context.current("VAULT_NAMESPACE") or "",
        required=False,
    )
    context.set_backend("VAULT_ADDR", addr)
    context.set_backend("VAULT_TOKEN", token, mask=True)
    if namespace:
        context.set_backend("VAULT_NAMESPACE", namespace)


def _collect_aws_key_storage(context: WizardContext, provider: InputProvider) -> None:
    region = provider.prompt_string(
        key="AWS_REGION",
        prompt="AWS region",
        default=context.current("AWS_REGION") or "us-east-1",
        required=True,
    )
    use_profile = provider.prompt_bool(
        key="AWS_USE_PROFILE",
        prompt="Use a named AWS profile?",
        default=bool(context.current("AWS_PROFILE")),
    )
    profile = ""
    access_key = ""
    secret_key = ""
    session_token = ""
    if use_profile:
        profile = provider.prompt_string(
            key="AWS_PROFILE",
            prompt="Profile name",
            default=context.current("AWS_PROFILE") or "",
            required=True,
        )
    else:
        access_key = provider.prompt_string(
            key="AWS_ACCESS_KEY_ID",
            prompt="AWS access key ID (optional if using instance profile)",
            default=context.current("AWS_ACCESS_KEY_ID") or "",
            required=False,
        )
        if access_key:
            secret_key = provider.prompt_secret(
                key="AWS_SECRET_ACCESS_KEY",
                prompt="AWS secret access key",
                existing=context.current("AWS_SECRET_ACCESS_KEY"),
                required=True,
            )
            session_token = provider.prompt_string(
                key="AWS_SESSION_TOKEN",
                prompt="AWS session token (optional)",
                default=context.current("AWS_SESSION_TOKEN") or "",
                required=False,
            )
        elif not is_headless_provider(provider):
            context.console.note(
                "Using IAM role/instance credentials (no static access keys provided).",
                topic="aws",
            )
        elif not access_key:
            raise CLIError(
                "AWS_ACCESS_KEY_ID is required when no profile is configured in headless mode."
            )

    context.set_backend("AWS_REGION", region)
    if profile:
        context.set_backend("AWS_PROFILE", profile)
    if access_key:
        context.set_backend("AWS_ACCESS_KEY_ID", access_key)
    if secret_key:
        context.set_backend("AWS_SECRET_ACCESS_KEY", secret_key, mask=True)
    if session_token:
        context.set_backend("AWS_SESSION_TOKEN", session_token)


def _collect_azure_key_storage(context: WizardContext, provider: InputProvider) -> None:
    vault_url = provider.prompt_string(
        key="AZURE_KEY_VAULT_URL",
        prompt="Key Vault URL (https://<name>.vault.azure.net/)",
        default=context.current("AZURE_KEY_VAULT_URL") or "",
        required=True,
    )
    tenant_id = provider.prompt_string(
        key="AZURE_TENANT_ID",
        prompt="Tenant ID (optional)",
        default=context.current("AZURE_TENANT_ID") or "",
        required=False,
    )
    client_id = provider.prompt_string(
        key="AZURE_CLIENT_ID",
        prompt="Client ID (optional)",
        default=context.current("AZURE_CLIENT_ID") or "",
        required=False,
    )
    client_secret = provider.prompt_secret(
        key="AZURE_CLIENT_SECRET",
        prompt="Client secret (optional)",
        existing=context.current("AZURE_CLIENT_SECRET"),
        required=False,
    )
    managed_identity_client_id = provider.prompt_string(
        key="AZURE_MANAGED_IDENTITY_CLIENT_ID",
        prompt="Managed identity client ID (optional)",
        default=context.current("AZURE_MANAGED_IDENTITY_CLIENT_ID") or "",
        required=False,
    )

    context.set_backend("AZURE_KEY_VAULT_URL", vault_url)
    if tenant_id:
        context.set_backend("AZURE_TENANT_ID", tenant_id)
    if client_id:
        context.set_backend("AZURE_CLIENT_ID", client_id)
    if client_secret:
        context.set_backend("AZURE_CLIENT_SECRET", client_secret, mask=True)
    if managed_identity_client_id:
        context.set_backend("AZURE_MANAGED_IDENTITY_CLIENT_ID", managed_identity_client_id)


def _collect_infisical_key_storage(
    context: WizardContext,
    provider: InputProvider,
    key_provider: SecretsProviderLiteral,
) -> None:
    default_base = (
        "https://app.infisical.com"
        if key_provider == SecretsProviderLiteral.INFISICAL_CLOUD
        else "http://localhost:8080"
    )
    base_url = provider.prompt_string(
        key="INFISICAL_BASE_URL",
        prompt="Infisical base URL",
        default=context.current("INFISICAL_BASE_URL") or default_base,
        required=True,
    )
    service_token = provider.prompt_secret(
        key="INFISICAL_SERVICE_TOKEN",
        prompt="Infisical service token",
        existing=context.current("INFISICAL_SERVICE_TOKEN"),
        required=True,
    )
    project_id = provider.prompt_string(
        key="INFISICAL_PROJECT_ID",
        prompt="Infisical project/workspace ID",
        default=context.current("INFISICAL_PROJECT_ID") or "",
        required=True,
    )
    environment = provider.prompt_string(
        key="INFISICAL_ENVIRONMENT",
        prompt="Infisical environment slug",
        default=context.current("INFISICAL_ENVIRONMENT") or "dev",
        required=True,
    )
    secret_path = provider.prompt_string(
        key="INFISICAL_SECRET_PATH",
        prompt="Secret path (e.g., /backend)",
        default=context.current("INFISICAL_SECRET_PATH") or "/",
        required=True,
    )
    ca_bundle = provider.prompt_string(
        key="INFISICAL_CA_BUNDLE_PATH",
        prompt="Custom CA bundle path (optional)",
        default=context.current("INFISICAL_CA_BUNDLE_PATH") or "",
        required=False,
    )

    context.set_backend("INFISICAL_BASE_URL", base_url)
    context.set_backend("INFISICAL_SERVICE_TOKEN", service_token, mask=True)
    context.set_backend("INFISICAL_PROJECT_ID", project_id)
    context.set_backend("INFISICAL_ENVIRONMENT", environment)
    context.set_backend("INFISICAL_SECRET_PATH", secret_path)
    if ca_bundle:
        context.set_backend("INFISICAL_CA_BUNDLE_PATH", ca_bundle)


def _ensure_vault_infra(context: WizardContext, enable_vault: bool) -> None:
    if context.infra_session:
        context.infra_session.ensure_vault(enabled=enable_vault)
    else:
        record = context.automation.get(AutomationPhase.SECRETS)
        if record.enabled and not enable_vault:
            context.automation.update(
                AutomationPhase.SECRETS,
                AutomationStatus.SKIPPED,
                "Vault automation skipped (verification disabled).",
            )
            context.refresh_automation_ui(AutomationPhase.SECRETS)


def _verify_vault_transit(context: WizardContext) -> None:
    base_url = context.require_env("VAULT_ADDR")
    token = context.require_env("VAULT_TOKEN")
    key_name = context.require_env("VAULT_TRANSIT_KEY")
    try:
        probe_vault_transit(base_url=base_url, token=token, key_name=key_name)
    except CLIError as exc:
        context.record_verification(
            provider=context.current("SECRETS_PROVIDER") or "vault",
            identifier=key_name,
            status="failed",
            detail=str(exc),
            source="wizard",
        )
        raise
    else:
        context.record_verification(
            provider=context.current("SECRETS_PROVIDER") or "vault",
            identifier=key_name,
            status="passed",
            detail=base_url,
            source="wizard",
        )
        context.console.success("Vault transit key verified.", topic="vault")


def _collect_vault(context: WizardContext, provider: InputProvider) -> bool:
    require_vault = context.profile in {"staging", "production"}
    enable_vault = provider.prompt_bool(
        key="VAULT_VERIFY_ENABLED",
        prompt="Enforce Vault Transit verification?",
        default=context.current_bool("VAULT_VERIFY_ENABLED", require_vault),
    )
    if require_vault and not enable_vault:
        raise CLIError("Vault verification is mandatory outside demo environments.")
    context.set_backend_bool("VAULT_VERIFY_ENABLED", enable_vault)
    if enable_vault:
        addr = provider.prompt_string(
            key="VAULT_ADDR",
            prompt="Vault address",
            default=context.current("VAULT_ADDR") or "https://vault.example.com",
            required=True,
        )
        token = provider.prompt_secret(
            key="VAULT_TOKEN",
            prompt="Vault token/AppRole secret",
            existing=context.current("VAULT_TOKEN"),
            required=True,
        )
        transit = provider.prompt_string(
            key="VAULT_TRANSIT_KEY",
            prompt="Vault Transit key name",
            default=context.current("VAULT_TRANSIT_KEY") or "auth-service",
            required=True,
        )
        context.set_backend("VAULT_ADDR", addr)
        context.set_backend("VAULT_TOKEN", token, mask=True)
        context.set_backend("VAULT_TRANSIT_KEY", transit)
    return enable_vault


def _force_verification_flag(context: WizardContext) -> None:
    require_vault = context.profile in {"staging", "production"}
    if require_vault:
        context.set_backend_bool("VAULT_VERIFY_ENABLED", True)
    elif context.current("VAULT_VERIFY_ENABLED") is None:
        context.set_backend_bool("VAULT_VERIFY_ENABLED", False)


def _rotate_signing_keys(context: WizardContext) -> None:
    result = handle_keys_rotate(argparse.Namespace(kid=None), context.cli_ctx)
    if result != 0:
        raise CLIError("Key rotation failed; see logs above.")
