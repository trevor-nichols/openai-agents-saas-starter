from __future__ import annotations

from collections.abc import Mapping

from starter_console.core import CLIError
from starter_console.core.constants import PROJECT_ROOT
from starter_console.core.status_models import ProbeResult, ProbeState
from starter_console.services.infra.backend_scripts import extract_json_payload, run_backend_script
from starter_console.services.sso.config import (
    env_key,
    parse_bool,
    resolve_enabled_providers,
)
from starter_console.workflows.home.probes.registry import ProbeContext

SCOPE_CHOICES = {"global", "tenant"}


def sso_probe(ctx: ProbeContext) -> ProbeResult:
    explicit_list = "SSO_PROVIDERS" in ctx.env
    try:
        provider_keys = resolve_enabled_providers(ctx.env)
    except CLIError as exc:
        detail = str(exc)
        reason = (
            "missing_providers_list"
            if "SSO_PROVIDERS" in detail
            else "invalid_provider_key"
        )
        remediation = (
            "Set SSO_PROVIDERS (empty value disables all providers)."
            if reason == "missing_providers_list"
            else "Fix SSO_PROVIDERS or provider key formatting."
        )
        return ProbeResult(
            name="sso",
            state=ProbeState.WARN if ctx.warn_only else ProbeState.ERROR,
            detail=detail,
            remediation=remediation,
            metadata={"providers": [], "reason": reason},
        )
    if not provider_keys:
        return ProbeResult(
            name="sso",
            state=ProbeState.SKIPPED,
            detail="sso disabled",
            metadata={"providers": [], "reason": "disabled"},
        )

    results: dict[str, ProbeResult] = {}
    for key in provider_keys:
        results[key] = _probe_provider(ctx, provider_key=key, assume_enabled=explicit_list)

    worst = max(results.values(), key=lambda item: item.severity_rank)
    failing = [
        provider
        for provider, result in results.items()
        if result.state in {ProbeState.ERROR, ProbeState.WARN}
    ]
    if not failing:
        detail = f"sso configured ({', '.join(provider_keys)})"
    else:
        detail = f"sso issues for: {', '.join(failing)}"

    metadata = {
        "providers": provider_keys,
        "results": {
            provider: {
                "state": result.state.value,
                "detail": result.detail,
                "remediation": result.remediation,
                **(result.metadata or {}),
            }
            for provider, result in results.items()
        },
    }

    return ProbeResult(
        name="sso",
        state=worst.state,
        detail=detail,
        metadata=metadata,
    )


def _probe_provider(
    ctx: ProbeContext,
    *,
    provider_key: str,
    assume_enabled: bool,
) -> ProbeResult:
    key = provider_key.strip().lower()
    enabled = parse_bool(ctx.env.get(env_key(key, "ENABLED")), default=assume_enabled)
    if not enabled:
        if assume_enabled:
            return ProbeResult(
                name="sso",
                state=ProbeState.WARN if ctx.warn_only else ProbeState.ERROR,
                detail="provider listed but disabled in env",
                remediation=f"Set {env_key(key, 'ENABLED')}=true or remove from SSO_PROVIDERS.",
                metadata={"provider": key, "reason": "disabled"},
            )
        return ProbeResult(
            name="sso",
            state=ProbeState.SKIPPED,
            detail="sso disabled",
            metadata={"provider": key, "reason": "disabled"},
        )

    scope_raw = (ctx.env.get(env_key(key, "SCOPE")) or "global").strip().lower()
    if scope_raw not in SCOPE_CHOICES:
        return _failure(
            ctx,
            detail=f"invalid scope '{scope_raw}'",
            remediation=f"Set {env_key(key, 'SCOPE')} to global or tenant.",
            metadata={"provider": key, "scope": scope_raw},
        )

    tenant_id = (ctx.env.get(env_key(key, "TENANT_ID")) or "").strip() or None
    tenant_slug = (ctx.env.get(env_key(key, "TENANT_SLUG")) or "").strip() or None
    if scope_raw == "global" and (tenant_id or tenant_slug):
        return _failure(
            ctx,
            detail="global scope should not include tenant id or slug",
            remediation=(
                f"Clear {env_key(key, 'TENANT_ID')}/{env_key(key, 'TENANT_SLUG')} "
                "or set scope=tenant."
            ),
            metadata={"provider": key, "scope": scope_raw},
        )
    if scope_raw == "tenant" and not (tenant_id or tenant_slug):
        return _failure(
            ctx,
            detail="tenant scope requires tenant id or slug",
            remediation=(
                f"Set {env_key(key, 'TENANT_ID')} or {env_key(key, 'TENANT_SLUG')}."
            ),
            metadata={"provider": key, "scope": scope_raw},
        )

    missing_env = _missing_prereqs(ctx.env)
    if missing_env:
        return _failure(
            ctx,
            detail=f"missing env: {', '.join(missing_env)}",
            remediation=(
                "Set AUTH_CACHE_REDIS_URL (or REDIS_URL) and a secret key "
                "(SSO_CLIENT_SECRET_ENCRYPTION_KEY, AUTH_SESSION_ENCRYPTION_KEY, or SECRET_KEY)."
            ),
            metadata={"provider": key, "scope": scope_raw, "missing": missing_env},
        )

    args = ["--provider", key]
    if tenant_id:
        args.extend(["--tenant-id", tenant_id])
    if tenant_slug:
        args.extend(["--tenant-slug", tenant_slug])

    completed = run_backend_script(
        project_root=PROJECT_ROOT,
        script_name="sso_status.py",
        args=args,
    )
    payload = _extract_payload(completed.stdout or "")
    if payload is None or completed.returncode != 0:
        detail = _format_backend_error(completed.stderr, completed.stdout, payload)
        return _failure(
            ctx,
            detail=detail,
            remediation="Check backend logs and database connectivity.",
            metadata={"provider": key, "scope": scope_raw},
        )

    result = str(payload.get("result") or "")
    metadata = _build_metadata(payload, provider=key, scope=scope_raw, tenant_slug=tenant_slug)
    if result == "not_configured":
        return ProbeResult(
            name="sso",
            state=ProbeState.WARN if ctx.warn_only else ProbeState.ERROR,
            detail="sso provider not configured",
            remediation="Run `starter-console sso setup` or seed provider config.",
            metadata=metadata,
        )

    if result != "ok":
        return _failure(
            ctx,
            detail=str(payload.get("detail") or "sso status failed"),
            remediation="Check backend logs and database connectivity.",
            metadata=metadata,
        )

    if not bool(payload.get("enabled", False)):
        return ProbeResult(
            name="sso",
            state=ProbeState.WARN if ctx.warn_only else ProbeState.ERROR,
            detail="sso provider disabled in database",
            remediation="Enable the provider or disable SSO in env.",
            metadata=metadata,
        )

    source = payload.get("config_source") or "unknown"
    detail = "sso configured"
    if scope_raw == "tenant" and source == "global":
        detail = "sso configured (global fallback)"
    elif source in {"tenant", "global"}:
        detail = f"sso configured ({source})"

    return ProbeResult(
        name="sso",
        state=ProbeState.OK,
        detail=detail,
        metadata=metadata,
    )


def _missing_prereqs(env: Mapping[str, str]) -> list[str]:
    missing: list[str] = []
    if not (env.get("AUTH_CACHE_REDIS_URL") or env.get("REDIS_URL")):
        missing.append("AUTH_CACHE_REDIS_URL or REDIS_URL")
    if not (
        env.get("SSO_CLIENT_SECRET_ENCRYPTION_KEY")
        or env.get("AUTH_SESSION_ENCRYPTION_KEY")
        or env.get("SECRET_KEY")
    ):
        missing.append(
            "SSO_CLIENT_SECRET_ENCRYPTION_KEY or AUTH_SESSION_ENCRYPTION_KEY or SECRET_KEY"
        )
    return missing


def _extract_payload(stdout: str) -> dict[str, object] | None:
    try:
        return extract_json_payload(stdout, required_keys=["result"])
    except Exception:
        return None


def _format_backend_error(
    stderr: str | None, stdout: str | None, payload: dict[str, object] | None
) -> str:
    if payload and payload.get("detail"):
        return str(payload.get("detail"))
    return (stderr or stdout or "backend script failed").strip()


def _build_metadata(
    payload: dict[str, object],
    *,
    provider: str,
    scope: str,
    tenant_slug: str | None,
) -> dict[str, object]:
    metadata = {
        "provider": provider,
        "scope": scope,
        "tenant_slug": tenant_slug,
        "config_source": payload.get("config_source"),
        "auto_provision_policy": payload.get("auto_provision_policy"),
        "default_role": payload.get("default_role"),
        "pkce_required": payload.get("pkce_required"),
        "token_auth_method": payload.get("token_auth_method"),
        "allowed_id_token_algs": payload.get("allowed_id_token_algs"),
        "allowed_domains_count": payload.get("allowed_domains_count"),
    }
    return {k: v for k, v in metadata.items() if v is not None}


def _failure(
    ctx: ProbeContext,
    *,
    detail: str,
    remediation: str,
    metadata: Mapping[str, object],
) -> ProbeResult:
    return ProbeResult(
        name="sso",
        state=ProbeState.WARN if ctx.warn_only else ProbeState.ERROR,
        detail=detail,
        remediation=remediation,
        metadata=dict(metadata),
    )


__all__ = ["sso_probe"]
