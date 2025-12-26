from __future__ import annotations

from collections.abc import Iterable, Mapping

from starter_contracts.secrets.models import SecretsProviderLiteral

from starter_console.core.status_models import ProbeResult, ProbeState
from starter_console.workflows.home.probes.registry import ProbeContext
from starter_console.workflows.home.probes.util import simple_result
from starter_console.workflows.home.probes.vault import vault_probe

SUPPORTED_PROVIDERS = {
    SecretsProviderLiteral.VAULT_DEV,
    SecretsProviderLiteral.VAULT_HCP,
    SecretsProviderLiteral.INFISICAL_CLOUD,
    SecretsProviderLiteral.INFISICAL_SELF_HOST,
    SecretsProviderLiteral.AWS_SM,
    SecretsProviderLiteral.AZURE_KV,
}


def secrets_probe(ctx: ProbeContext) -> ProbeResult:
    provider_raw = ctx.env.get("SECRETS_PROVIDER")
    provider = _parse_provider(provider_raw)
    if provider is None:
        return ProbeResult(
            name="secrets",
            state=ProbeState.SKIPPED,
            detail="secrets provider not configured",
            metadata={"provider": provider_raw or "unset"},
        )

    if provider in (SecretsProviderLiteral.VAULT_DEV, SecretsProviderLiteral.VAULT_HCP):
        return _wrap("vault", provider_raw, vault_probe(warn_only=ctx.warn_only))

    if provider in (
        SecretsProviderLiteral.INFISICAL_CLOUD,
        SecretsProviderLiteral.INFISICAL_SELF_HOST,
    ):
        return _infisical_probe(ctx, provider_raw)

    if provider is SecretsProviderLiteral.AWS_SM:
        return _aws_sm_probe(ctx, provider_raw)

    if provider is SecretsProviderLiteral.AZURE_KV:
        return _azure_kv_probe(ctx, provider_raw)

    return ProbeResult(
        name="secrets",
        state=ProbeState.SKIPPED,
        detail="secrets provider not supported",
        metadata={"provider": provider_raw or "unset"},
    )


# ---------------------------------------------------------------------------
# Provider-specific helpers
# ---------------------------------------------------------------------------

def _infisical_probe(ctx: ProbeContext, provider_raw: str | None) -> ProbeResult:
    required = ("INFISICAL_PROJECT_ID", "INFISICAL_ENVIRONMENT", "INFISICAL_SERVICE_TOKEN")
    missing = _missing_keys(ctx.env, required)
    if missing:
        return _missing_env_result(provider_raw, missing, ctx.warn_only)

    base_url = ctx.env.get("INFISICAL_BASE_URL", "https://app.infisical.com")
    return simple_result(
        name="secrets",
        success=True,
        detail="infisical configured",
        metadata={"provider": provider_raw, "base_url": base_url},
    )


def _aws_sm_probe(ctx: ProbeContext, provider_raw: str | None) -> ProbeResult:
    region = ctx.env.get("AWS_REGION")
    has_keys = bool(ctx.env.get("AWS_ACCESS_KEY_ID") and ctx.env.get("AWS_SECRET_ACCESS_KEY"))
    has_profile = bool(ctx.env.get("AWS_PROFILE"))
    missing = []
    if not region:
        missing.append("AWS_REGION")
    if not (has_keys or has_profile):
        missing.extend(["AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY or AWS_PROFILE"])

    if missing:
        return _missing_env_result(provider_raw, missing, ctx.warn_only)

    return simple_result(
        name="secrets",
        success=True,
        detail="aws secrets manager configured",
        metadata={
            "provider": provider_raw,
            "region": region,
            "auth": "keys" if has_keys else "profile",
        },
    )


def _azure_kv_probe(ctx: ProbeContext, provider_raw: str | None) -> ProbeResult:
    vault_url = ctx.env.get("AZURE_KEY_VAULT_URL") or ctx.env.get("AZURE_KEY_VAULT_NAME")
    client_id = ctx.env.get("AZURE_CLIENT_ID")
    client_secret = ctx.env.get("AZURE_CLIENT_SECRET")
    tenant_id = ctx.env.get("AZURE_TENANT_ID")
    managed_id = ctx.env.get("AZURE_MANAGED_IDENTITY_CLIENT_ID")

    missing = []
    if not vault_url:
        missing.append("AZURE_KEY_VAULT_URL")
    auth_ok = bool(managed_id or (client_id and client_secret and tenant_id))
    if not auth_ok:
        missing.append(
            "AZURE_CLIENT_ID/AZURE_CLIENT_SECRET/AZURE_TENANT_ID"
            " or AZURE_MANAGED_IDENTITY_CLIENT_ID"
        )

    if missing:
        return _missing_env_result(provider_raw, missing, ctx.warn_only)

    auth_mode = "managed_identity" if managed_id else "client_secret"
    return simple_result(
        name="secrets",
        success=True,
        detail="azure key vault configured",
        metadata={"provider": provider_raw, "vault": vault_url, "auth": auth_mode},
    )


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _parse_provider(raw: str | None) -> SecretsProviderLiteral | None:
    if not raw:
        return None
    try:
        value = SecretsProviderLiteral(raw)
    except Exception:
        return None
    return value if value in SUPPORTED_PROVIDERS else None


def _missing_keys(env: Mapping[str, str], keys: Iterable[str]) -> list[str]:
    return sorted(key for key in keys if not env.get(key))


def _missing_env_result(
    provider_raw: str | None, missing: Iterable[str], warn_only: bool
) -> ProbeResult:
    missing_list = list(missing)
    detail = f"missing env: {', '.join(missing_list)}"
    return ProbeResult(
        name="secrets",
        state=ProbeState.WARN if warn_only else ProbeState.ERROR,
        detail=detail,
        remediation="Populate required secrets provider env vars or switch provider.",
        metadata={"provider": provider_raw, "missing": missing_list},
    )


def _wrap(provider_name: str, provider_raw: str | None, result: ProbeResult) -> ProbeResult:
    """Rename underlying provider probe to 'secrets' while keeping metadata."""
    base_metadata = dict(result.metadata) if result.metadata else {}
    base_metadata["provider"] = provider_raw or provider_name
    return ProbeResult(
        name="secrets",
        state=result.state,
        detail=result.detail,
        remediation=result.remediation,
        duration_ms=result.duration_ms,
        metadata=base_metadata,
        created_at=result.created_at,
    )


__all__ = ["secrets_probe"]
