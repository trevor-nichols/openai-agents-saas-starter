from __future__ import annotations

import argparse

from starter_shared.secrets.models import SecretsProviderLiteral

from starter_cli.cli.auth_commands import handle_keys_rotate
from starter_cli.cli.common import CLIError
from starter_cli.cli.console import console
from starter_cli.cli.secrets import registry
from starter_cli.cli.setup._wizard.context import WizardContext
from starter_cli.cli.setup.automation import AutomationPhase, AutomationStatus
from starter_cli.cli.setup.inputs import HeadlessInputProvider, InputProvider
from starter_cli.cli.setup.validators import probe_vault_transit

_VAULT_PROVIDERS = {
    SecretsProviderLiteral.VAULT_DEV,
    SecretsProviderLiteral.VAULT_HCP,
}


def run(context: WizardContext, provider: InputProvider) -> None:
    console.info("[M1] Secrets & Vault", topic="wizard")
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
            if isinstance(provider, HeadlessInputProvider):
                raise CLIError(f"Invalid secrets provider '{choice}'.") from None
            console.warn(
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

    from starter_cli.cli.secrets.models import SecretsWorkflowOptions

    runner = registry.get_runner(literal)
    result = runner(context.cli_ctx, provider, options=SecretsWorkflowOptions(skip_make=True))
    for key, value in result.env_updates.items():
        context.set_backend(key, value)


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
        console.success("Vault transit key verified.", topic="vault")


def _collect_vault(context: WizardContext, provider: InputProvider) -> bool:
    require_vault = context.profile in {"staging", "production"}
    enable_vault = provider.prompt_bool(
        key="VAULT_VERIFY_ENABLED",
        prompt="Enforce Vault Transit verification?",
        default=context.current_bool("VAULT_VERIFY_ENABLED", require_vault),
    )
    if require_vault and not enable_vault:
        raise CLIError("Vault verification is mandatory outside local environments.")
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
