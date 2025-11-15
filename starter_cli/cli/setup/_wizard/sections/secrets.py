from __future__ import annotations

import argparse

from starter_cli.cli.auth_commands import handle_keys_rotate
from starter_cli.cli.common import CLIError
from starter_cli.cli.console import console
from starter_cli.cli.setup._wizard.context import WizardContext
from starter_cli.cli.setup.inputs import InputProvider
from starter_cli.cli.setup.validators import probe_vault_transit


def run(context: WizardContext, provider: InputProvider) -> None:
    console.info("[M1] Secrets & Vault", topic="wizard")
    _collect_secrets(context, provider)

    rotate = provider.prompt_bool(
        key="ROTATE_SIGNING_KEYS",
        prompt="Rotate the Ed25519 signing keyset now?",
        default=False,
    )
    if rotate:
        _rotate_signing_keys(context)

    _collect_vault(context, provider)
    if context.current_bool("VAULT_VERIFY_ENABLED", False):
        probe_vault_transit(
            base_url=context.require_env("VAULT_ADDR"),
            token=context.require_env("VAULT_TOKEN"),
            key_name=context.require_env("VAULT_TRANSIT_KEY"),
        )
        console.success("Vault transit key verified.", topic="vault")


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


def _collect_vault(context: WizardContext, provider: InputProvider) -> None:
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


def _rotate_signing_keys(context: WizardContext) -> None:
    result = handle_keys_rotate(argparse.Namespace(kid=None), context.cli_ctx)
    if result != 0:
        raise CLIError("Key rotation failed; see logs above.")
