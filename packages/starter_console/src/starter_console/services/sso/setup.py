from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from starter_console.adapters.env import EnvFile
from starter_console.core import CLIContext, CLIError
from starter_console.services.infra.backend_scripts import (
    extract_json_payload,
    merge_env_files,
    resolve_backend_env_files,
    run_backend_script,
)

from .config import (
    SsoProviderSeedConfig,
    env_key,
    parse_bool,
)


@dataclass(slots=True)
class SsoSetupResult:
    result: str
    provider_key: str
    tenant_id: str | None
    tenant_slug: str | None
    config_id: str | None


def load_env_values(ctx: CLIContext) -> dict[str, str]:
    env_files = resolve_backend_env_files(ctx.project_root, ctx=ctx)
    return merge_env_files(env_files)


def update_backend_env(project_root: Path, config: SsoProviderSeedConfig) -> None:
    env_path = project_root / "apps" / "api-service" / ".env.local"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env = EnvFile(env_path)

    def _set(key: str, value: str | None) -> None:
        env.set(key, value or "")

    _set(env_key(config.provider_key, "ENABLED"), "true" if config.enabled else "false")
    _set(env_key(config.provider_key, "SCOPE"), config.tenant_scope)
    _set(env_key(config.provider_key, "TENANT_ID"), config.tenant_id)
    _set(env_key(config.provider_key, "TENANT_SLUG"), config.tenant_slug)
    _set(env_key(config.provider_key, "ISSUER_URL"), config.issuer_url)
    _set(env_key(config.provider_key, "DISCOVERY_URL"), config.discovery_url)
    _set(env_key(config.provider_key, "CLIENT_ID"), config.client_id)
    if config.clear_client_secret:
        _set(env_key(config.provider_key, "CLIENT_SECRET"), "")
    elif config.client_secret is not None:
        _set(env_key(config.provider_key, "CLIENT_SECRET"), config.client_secret)
    _set(env_key(config.provider_key, "SCOPES"), ",".join(config.scopes))
    _set(
        env_key(config.provider_key, "PKCE_REQUIRED"),
        "true" if config.pkce_required else "false",
    )
    _set(env_key(config.provider_key, "TOKEN_AUTH_METHOD"), config.token_auth_method)
    _set(
        env_key(config.provider_key, "ID_TOKEN_ALGS"),
        ",".join(config.allowed_id_token_algs),
    )
    _set(env_key(config.provider_key, "AUTO_PROVISION_POLICY"), config.auto_provision_policy)
    _set(env_key(config.provider_key, "ALLOWED_DOMAINS"), ",".join(config.allowed_domains))
    _set(env_key(config.provider_key, "DEFAULT_ROLE"), config.default_role)

    env.save()


def update_backend_env_providers(project_root: Path, provider_keys: list[str]) -> None:
    env_path = project_root / "apps" / "api-service" / ".env.local"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env = EnvFile(env_path)
    providers_value = ",".join(provider_keys)
    env.set("SSO_PROVIDERS", providers_value)
    env.save()


def run_sso_setup(
    ctx: CLIContext,
    *,
    config: SsoProviderSeedConfig,
    update_env: bool = True,
) -> SsoSetupResult:
    if config.token_auth_method == "none" and not config.pkce_required:
        raise CLIError("token_auth_method=none requires PKCE.")
    if update_env:
        update_backend_env(ctx.project_root, config)
        ctx.console.success(
            "SSO settings persisted to apps/api-service/.env.local",
            topic="sso",
        )

    completed = run_backend_script(
        project_root=ctx.project_root,
        script_name="seed_sso_provider.py",
        args=config.to_script_args(),
        ctx=ctx,
    )
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        detail = stderr or stdout or "unknown error"
        raise CLIError(f"SSO seed failed: {detail}")

    payload = extract_json_payload(completed.stdout or "", required_keys=["result"])
    ctx.console.success(
        f"SSO provider {config.provider_key} seeded ({payload.get('result')}).",
        topic="sso",
    )
    summary = json.dumps(payload, indent=2)
    ctx.console.info("SSO seed summary:", topic="sso")
    ctx.console.print(summary)

    return SsoSetupResult(
        result=str(payload.get("result")),
        provider_key=str(payload.get("provider_key")),
        tenant_id=payload.get("tenant_id"),
        tenant_slug=payload.get("tenant_slug"),
        config_id=payload.get("config_id"),
    )


def resolve_enabled_flag(*, provided: bool | None, existing: str | None) -> bool:
    if provided is not None:
        return bool(provided)
    if existing is not None:
        return parse_bool(existing, default=True)
    return True


__all__ = [
    "SsoSetupResult",
    "load_env_values",
    "resolve_enabled_flag",
    "run_sso_setup",
    "update_backend_env",
    "update_backend_env_providers",
]
