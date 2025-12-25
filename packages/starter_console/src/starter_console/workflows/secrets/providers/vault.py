from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from starter_contracts.secrets.models import SecretsProviderLiteral

from starter_console.core import CLIContext
from starter_console.telemetry import VerificationArtifact

from ..models import OnboardResult, SecretsWorkflowOptions

if TYPE_CHECKING:
    from starter_console.workflows.setup.inputs import InputProvider


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
        "Run `just vault-up` to start the local dev signer (remains in-memory, non-production).",
        "Export the variables above or add them to apps/api-service/.env.local / .env.compose.",
        "Re-run `just verify-vault` after updating FastAPI env to ensure end-to-end signing works.",
    ]

    if not options.skip_automation:
        auto_start = provider.prompt_bool(
            key="VAULT_DEV_AUTO_START",
            prompt="Run `just vault-up` now?",
            default=True,
        )
        if auto_start:
            _run_just_recipe(ctx, ctx.console, "vault-up", topic="secrets")
            steps[0] = "Started the dev signer via `just vault-up`."

    warnings: list[str] = [
        (
            "Dev Vault stores state in-memory with a static root token. "
            "Never expose it to production traffic."
        )
    ]

    artifacts = [
        VerificationArtifact(
            provider="vault_dev",
            identifier=transit_key,
            status="pending",
            detail=f"{addr} (manual verification required)",
            source="secrets.onboard",
        )
    ]

    return OnboardResult(
        provider=SecretsProviderLiteral.VAULT_DEV,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
        artifacts=artifacts,
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
        "Run `just verify-vault` (pointed at the HCP cluster) to smoke test signatures.",
    ]

    warnings = [
        (
            "HCP Vault enforces TLS + namespaces; confirm your VAULT_NAMESPACE "
            "matches the cluster settings."
        ),
        "Store the Vault token/AppRole secret in your password manager or secure secret store.",
    ]

    artifacts = [
        VerificationArtifact(
            provider="vault_hcp",
            identifier=f"{namespace}:{transit_key}",
            status="pending",
            detail=f"{addr} (manual verification required)",
            source="secrets.onboard",
        )
    ]

    return OnboardResult(
        provider=SecretsProviderLiteral.VAULT_HCP,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
        artifacts=artifacts,
    )


def _run_just_recipe(ctx: CLIContext, console, target: str, *, topic: str) -> None:
    console.info(f"Running `just {target}` …", topic=topic)
    subprocess.run(["just", target], cwd=ctx.project_root, check=True)


__all__ = ["run_vault_dev", "run_vault_hcp"]
