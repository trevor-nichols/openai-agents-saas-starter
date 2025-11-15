from __future__ import annotations

import subprocess

from starter_shared.secrets.models import SecretsProviderLiteral

from ...common import CLIContext
from ...console import console
from ...setup.inputs import InputProvider
from ..models import OnboardResult, SecretsWorkflowOptions


def run_vault_dev(
    ctx: CLIContext,
    provider: InputProvider,
    *,
    options: SecretsWorkflowOptions,
) -> OnboardResult:
    settings = ctx.optional_settings()
    default_addr = (settings.vault_addr if settings else None) or "http://127.0.0.1:18200"
    default_token = (settings.vault_token if settings else None) or "vault-dev-root"
    default_transit = settings.vault_transit_key if settings else "auth-service"

    addr = provider.prompt_string(
        key="VAULT_ADDR",
        prompt="Vault dev address",
        default=default_addr,
        required=True,
    )
    token = provider.prompt_secret(
        key="VAULT_TOKEN",
        prompt="Vault token",
        existing=default_token,
        required=True,
    )
    transit_key = provider.prompt_string(
        key="VAULT_TRANSIT_KEY",
        prompt="Transit key name",
        default=default_transit,
        required=True,
    )
    verify = provider.prompt_bool(
        key="VAULT_VERIFY_ENABLED",
        prompt="Enforce Vault verification for service-account issuance?",
        default=True,
    )

    env_updates = {
        "SECRETS_PROVIDER": SecretsProviderLiteral.VAULT_DEV.value,
        "VAULT_ADDR": addr,
        "VAULT_TOKEN": token,
        "VAULT_TRANSIT_KEY": transit_key,
        "VAULT_VERIFY_ENABLED": "true" if verify else "false",
    }

    steps = [
        "Run `make vault-up` to start the local dev signer (remains in-memory, non-production).",
        "Export the variables above or add them to .env.local / .env.compose.",
        "Re-run `make verify-vault` after updating FastAPI env to ensure end-to-end signing works.",
    ]

    if not options.skip_make and _prompt_yes_no("Run `make vault-up` now?", default=True):
        _run_make_target(ctx, "vault-up", topic="secrets")
        steps[0] = "Started the dev signer via `make vault-up`."

    warnings: list[str] = [
        (
            "Dev Vault stores state in-memory with a static root token. "
            "Never expose it to production traffic."
        )
    ]

    return OnboardResult(
        provider=SecretsProviderLiteral.VAULT_DEV,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
    )


def run_vault_hcp(
    ctx: CLIContext,
    provider: InputProvider,
    *,
    options: SecretsWorkflowOptions,
) -> OnboardResult:  # pragma: no cover - simple wrapper, exercised via CLI tests
    settings = ctx.optional_settings()
    default_addr = settings.vault_addr if settings and settings.vault_addr else ""
    default_namespace = (
        settings.vault_namespace if settings and settings.vault_namespace else "admin"
    )
    default_transit = settings.vault_transit_key if settings else "auth-service"

    addr = provider.prompt_string(
        key="VAULT_ADDR",
        prompt="HCP Vault address (https://...:8200)",
        default=default_addr or None,
        required=True,
    )
    namespace = provider.prompt_string(
        key="VAULT_NAMESPACE",
        prompt="Vault namespace (admin/tenant)",
        default=default_namespace,
        required=True,
    )
    token = provider.prompt_secret(
        key="VAULT_TOKEN",
        prompt="Vault token/AppRole secret",
        existing=settings.vault_token if settings else None,
        required=True,
    )
    transit_key = provider.prompt_string(
        key="VAULT_TRANSIT_KEY",
        prompt="Transit key name",
        default=default_transit,
        required=True,
    )
    verify = provider.prompt_bool(
        key="VAULT_VERIFY_ENABLED",
        prompt="Enforce Vault verification for service-account issuance?",
        default=True,
    )

    env_updates = {
        "SECRETS_PROVIDER": SecretsProviderLiteral.VAULT_HCP.value,
        "VAULT_ADDR": addr,
        "VAULT_NAMESPACE": namespace,
        "VAULT_TOKEN": token,
        "VAULT_TRANSIT_KEY": transit_key,
        "VAULT_VERIFY_ENABLED": "true" if verify else "false",
    }

    steps = [
        "Ensure the Transit secrets engine is enabled and the specified key exists.",
        "Configure a minimally scoped token/AppRole with transit:sign + transit:verify.",
        "Update backend/CLI env files with the values above and restart FastAPI.",
        "Run `make verify-vault` (pointed at the HCP cluster) to smoke test signatures.",
    ]

    warnings = [
        (
            "HCP Vault enforces TLS + namespaces; confirm your VAULT_NAMESPACE "
            "matches the cluster settings."
        ),
        "Store the Vault token/AppRole secret in your password manager or secure secret store.",
    ]

    return OnboardResult(
        provider=SecretsProviderLiteral.VAULT_HCP,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
    )


def _prompt_yes_no(question: str, *, default: bool) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{question} ({hint}) ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        console.warn("Please answer yes or no.", topic="secrets")


def _run_make_target(ctx: CLIContext, target: str, *, topic: str) -> None:
    console.info(f"Running `make {target}` …", topic=topic)
    subprocess.run(["make", target], cwd=ctx.project_root, check=True)


__all__ = ["run_vault_dev", "run_vault_hcp"]
