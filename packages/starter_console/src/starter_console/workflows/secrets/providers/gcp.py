from __future__ import annotations

from typing import TYPE_CHECKING

from starter_contracts.secrets.models import SecretsProviderLiteral
from starter_providers.secrets import GCPSecretManagerClient, GCPSecretManagerError

from starter_console.core import CLIContext, CLIError
from starter_console.telemetry import VerificationArtifact

from ..models import OnboardResult, SecretsWorkflowOptions

if TYPE_CHECKING:
    from starter_console.workflows.setup.inputs import InputProvider


def run_gcp_sm(
    ctx: CLIContext,
    provider: InputProvider,
    *,
    options: SecretsWorkflowOptions,
) -> OnboardResult:
    settings = ctx.optional_settings()
    defaults = settings.gcp_settings if settings else None

    project_id = provider.prompt_string(
        key="GCP_SM_PROJECT_ID",
        prompt="GCP project ID (optional if secret name is fully qualified)",
        default=defaults.project_id if defaults and defaults.project_id else "",
        required=False,
    )
    secret_name_default = (
        defaults.signing_secret_name if defaults and defaults.signing_secret_name else None
    )
    signing_secret = provider.prompt_string(
        key="GCP_SM_SIGNING_SECRET_NAME",
        prompt="Secret Manager secret name for signing",
        default=secret_name_default or "auth-signing-secret",
        required=True,
    )
    if not project_id and not signing_secret.strip().startswith("projects/"):
        raise CLIError(
            "GCP_SM_PROJECT_ID is required when GCP_SM_SIGNING_SECRET_NAME is not fully qualified."
        )

    cache_ttl_raw = provider.prompt_string(
        key="GCP_SM_CACHE_TTL_SECONDS",
        prompt="Secret cache TTL (seconds)",
        default=str(defaults.cache_ttl_seconds if defaults else 60),
        required=True,
    )
    cache_ttl = _coerce_positive_int(cache_ttl_raw, "GCP_SM_CACHE_TTL_SECONDS")

    verified = False
    if options.skip_verification:
        ctx.console.info(
            "Skipping GCP Secret Manager verification (external calls disabled).",
            topic="secrets",
        )
    else:
        verified = _probe_gcp_secret(
            project_id=project_id or None,
            secret_name=signing_secret,
            console=ctx.console,
        )

    env_updates = {
        "SECRETS_PROVIDER": SecretsProviderLiteral.GCP_SM.value,
        "GCP_SM_SIGNING_SECRET_NAME": signing_secret,
        "GCP_SM_CACHE_TTL_SECONDS": str(cache_ttl),
        "VAULT_VERIFY_ENABLED": "true",
    }
    if project_id:
        env_updates["GCP_SM_PROJECT_ID"] = project_id

    steps = [
        "Ensure the signing secret exists in Secret Manager.",
        "Grant the runtime service account roles/secretmanager.secretAccessor.",
        "Store the env vars above and restart FastAPI.",
    ]
    warnings: list[str] = []
    if verified:
        steps.insert(0, "Validated Secret Manager access by reading the signing secret.")
    else:
        if options.skip_verification:
            message = "Secret Manager verification skipped."
        else:
            message = (
                "Failed to read the signing secret via Secret Manager. "
                "Check IAM or credentials (ADC/GOOGLE_APPLICATION_CREDENTIALS)."
            )
        warnings.append(message)

    artifacts = [
        VerificationArtifact(
            provider="gcp_sm",
            identifier=signing_secret,
            status="passed" if verified else "failed",
            detail=f"project={project_id}" if project_id else None,
            source="secrets.onboard",
        )
    ]

    return OnboardResult(
        provider=SecretsProviderLiteral.GCP_SM,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
        artifacts=artifacts,
    )


def _probe_gcp_secret(
    *,
    project_id: str | None,
    secret_name: str,
    console,
) -> bool:
    try:
        client = GCPSecretManagerClient(project_id=project_id)
        client.get_secret_value(secret_name)
        return True
    except GCPSecretManagerError as exc:  # pragma: no cover - external API dependency
        console.warn(f"GCP probe failed: {exc}", topic="secrets")
        return False


def _coerce_positive_int(value: str, label: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise CLIError(f"{label} must be an integer.") from exc
    if parsed <= 0:
        raise CLIError(f"{label} must be greater than zero.")
    return parsed


__all__ = ["run_gcp_sm"]
