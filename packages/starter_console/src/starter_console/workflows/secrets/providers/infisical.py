from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from starter_contracts.secrets.models import SecretsProviderLiteral

from starter_console.core import CLIContext
from starter_console.telemetry import VerificationArtifact

from ..models import OnboardResult, SecretsWorkflowOptions

if TYPE_CHECKING:
    from starter_console.workflows.setup.inputs import InputProvider


def run_infisical_cloud(
    ctx: CLIContext,
    provider: InputProvider,
    *,
    options: SecretsWorkflowOptions,
) -> OnboardResult:
    return _run_infisical_flow(
        ctx,
        provider,
        console=ctx.console,
        default_base_url="https://app.infisical.com",
        label="Infisical Cloud",
        prompt_ca_bundle=False,
        skip_verification=options.skip_verification,
    )


def run_infisical_self_hosted(
    ctx: CLIContext,
    provider: InputProvider,
    *,
    options: SecretsWorkflowOptions,
) -> OnboardResult:
    return _run_infisical_flow(
        ctx,
        provider,
        console=ctx.console,
        default_base_url="http://localhost:8080",
        label="Infisical Self-Hosted",
        prompt_ca_bundle=True,
        skip_verification=options.skip_verification,
    )


def _run_infisical_flow(
    ctx: CLIContext,
    provider: InputProvider,
    *,
    console,
    default_base_url: str,
    label: str,
    prompt_ca_bundle: bool,
    skip_verification: bool,
) -> OnboardResult:
    settings = ctx.optional_settings()
    defaults = settings.infisical_settings if settings else None
    base_url = provider.prompt_string(
        key="INFISICAL_BASE_URL",
        prompt=f"{label} base URL",
        default=(defaults.base_url if defaults and defaults.base_url else default_base_url),
        required=True,
    )
    service_token = provider.prompt_secret(
        key="INFISICAL_SERVICE_TOKEN",
        prompt="Infisical service token",
        existing=defaults.service_token if defaults else None,
        required=True,
    )
    project_id = provider.prompt_string(
        key="INFISICAL_PROJECT_ID",
        prompt="Infisical project/workspace ID",
        default=defaults.project_id if defaults and defaults.project_id else None,
        required=True,
    )
    environment = provider.prompt_string(
        key="INFISICAL_ENVIRONMENT",
        prompt="Infisical environment slug",
        default=(defaults.environment if defaults and defaults.environment else "dev"),
        required=True,
    )
    secret_path = provider.prompt_string(
        key="INFISICAL_SECRET_PATH",
        prompt="Secret path (e.g., /backend)",
        default=defaults.secret_path if defaults and defaults.secret_path else "/",
        required=True,
    )
    signing_secret = provider.prompt_string(
        key="INFISICAL_SIGNING_SECRET_NAME",
        prompt="Signing secret name",
        default=(
            defaults.signing_secret_name if defaults else "auth-service-signing-secret"
        ),
        required=True,
    )
    ca_bundle = ""
    if prompt_ca_bundle:
        ca_bundle = provider.prompt_string(
            key="INFISICAL_CA_BUNDLE_PATH",
            prompt="Custom CA bundle path (leave blank for default trust store)",
            default=defaults.ca_bundle_path if defaults and defaults.ca_bundle_path else "",
            required=False,
        )

    env_updates = {
        "SECRETS_PROVIDER": (
            SecretsProviderLiteral.INFISICAL_SELF_HOST.value
            if prompt_ca_bundle
            else SecretsProviderLiteral.INFISICAL_CLOUD.value
        ),
        "INFISICAL_BASE_URL": base_url,
        "INFISICAL_SERVICE_TOKEN": service_token,
        "INFISICAL_PROJECT_ID": project_id,
        "INFISICAL_ENVIRONMENT": environment,
        "INFISICAL_SECRET_PATH": secret_path,
        "INFISICAL_SIGNING_SECRET_NAME": signing_secret,
        "VAULT_VERIFY_ENABLED": "true",
    }
    if ca_bundle:
        env_updates["INFISICAL_CA_BUNDLE_PATH"] = ca_bundle

    verified = False
    if skip_verification:
        console.info(
            "Skipping Infisical verification (external calls disabled).",
            topic="secrets",
        )
    else:
        verified = _probe_infisical_secret(
            base_url=base_url,
            service_token=service_token,
            project_id=project_id,
            environment=environment,
            secret_path=secret_path,
            secret_name=signing_secret,
            ca_bundle_path=ca_bundle or None,
            console=console,
        )

    steps = [
        "Install the Infisical CLI or configure service tokens for CI/CD.",
        "Store the service token securely (rotate via Infisical dashboard).",
        (
            "Add the env vars above to apps/api-service/.env and apps/api-service/.env.local, "
            "then restart FastAPI + CLI shells."
        ),
    ]
    warnings: list[str] = []

    if verified:
        steps.insert(
            0,
            f"Validated that secret `{signing_secret}` exists and is readable.",
        )
    else:
        if skip_verification:
            message = "Infisical verification skipped."
        else:
            message = (
                "Could not verify the signing secret via the Infisical API. "
                "Double-check the service token permissions and secret name."
            )
        warnings.append(message)

    provider_literal = (
        SecretsProviderLiteral.INFISICAL_SELF_HOST
        if prompt_ca_bundle
        else SecretsProviderLiteral.INFISICAL_CLOUD
    )
    artifacts = [
        VerificationArtifact(
            provider=provider_literal.value,
            identifier=f"{project_id}:{secret_path}:{signing_secret}",
            status="passed" if verified else "failed",
            detail=f"{base_url} ({environment})",
            source="secrets.onboard",
        )
    ]

    return OnboardResult(
        provider=provider_literal,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
        artifacts=artifacts,
    )


def _probe_infisical_secret(
    *,
    base_url: str,
    service_token: str,
    project_id: str,
    environment: str,
    secret_path: str,
    secret_name: str,
    ca_bundle_path: str | None,
    console,
) -> bool:
    params = {
        "environment": environment,
        "workspaceId": project_id,
        "type": "shared",
        "path": secret_path or "/",
    }
    headers = {"Authorization": f"Bearer {service_token}"}
    verify: bool | str = ca_bundle_path or True
    url = f"{base_url.rstrip('/')}/api/v4/secrets/{secret_name}"
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=5.0, verify=verify)
    except httpx.HTTPError as exc:  # pragma: no cover - network failure path
        console.warn(f"Infisical probe failed: {exc}", topic="secrets")
        return False

    if response.status_code == 200:
        return True
    if response.status_code == 404:
        return False
    console.warn(
        f"Infisical probe returned {response.status_code}: {response.text}",
        topic="secrets",
    )
    return False


__all__ = ["run_infisical_cloud", "run_infisical_self_hosted"]
