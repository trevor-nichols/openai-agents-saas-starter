from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass

from starter_console.core import CLIError

from .constants import (
    AUTO_PROVISION_POLICIES,
    DEFAULT_AUTO_PROVISION_POLICY,
    DEFAULT_ROLE,
    DEFAULT_SCOPE_MODE,
    DEFAULT_SCOPES,
    DEFAULT_TOKEN_AUTH_METHOD,
    ID_TOKEN_ALG_CHOICES,
    ROLE_CHOICES,
    SCOPE_MODE_CHOICES,
    TOKEN_AUTH_METHOD_CHOICES,
)


def env_key(provider_key: str, suffix: str) -> str:
    return f"SSO_{provider_key.strip().upper()}_{suffix}"


@dataclass(slots=True)
class SsoProviderSeedConfig:
    provider_key: str
    enabled: bool
    tenant_scope: str
    tenant_id: str | None
    tenant_slug: str | None
    issuer_url: str
    client_id: str
    client_secret: str | None
    discovery_url: str | None
    scopes: list[str]
    pkce_required: bool
    token_auth_method: str
    allowed_id_token_algs: list[str]
    auto_provision_policy: str
    allowed_domains: list[str]
    default_role: str

    def to_script_args(self) -> list[str]:
        args = [
            "--provider",
            self.provider_key,
            "--issuer-url",
            self.issuer_url,
            "--client-id",
            self.client_id,
            "--auto-provision-policy",
            self.auto_provision_policy,
            "--default-role",
            self.default_role,
            "--scopes",
            ",".join(self.scopes),
        ]
        if not self.enabled:
            args.append("--disable")
        if self.discovery_url:
            args.extend(["--discovery-url", self.discovery_url])
        if self.tenant_id:
            args.extend(["--tenant-id", self.tenant_id])
        if self.tenant_slug:
            args.extend(["--tenant-slug", self.tenant_slug])
        if self.client_secret:
            args.extend(["--client-secret", self.client_secret])
        if self.allowed_domains:
            args.extend(["--allowed-domains", ",".join(self.allowed_domains)])
        if self.allowed_id_token_algs:
            args.extend(["--id-token-algs", ",".join(self.allowed_id_token_algs)])
        if self.token_auth_method:
            args.extend(["--token-auth-method", self.token_auth_method])
        if self.pkce_required:
            args.append("--pkce-required")
        else:
            args.append("--no-pkce")
        return args


def parse_bool(raw: str | None, *, default: bool = False) -> bool:
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y"}


def parse_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    value = str(raw).strip()
    if not value:
        return []
    if value.startswith("["):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise CLIError(f"Invalid JSON list: {exc}") from exc
        if not isinstance(parsed, list):
            raise CLIError("Expected a JSON list.")
        return [str(item).strip() for item in parsed if str(item).strip()]
    if "," in value:
        return [item.strip() for item in value.split(",") if item.strip()]
    return [item.strip() for item in value.split() if item.strip()]


def parse_scopes(raw: str | None) -> list[str]:
    scopes = parse_list(raw)
    return scopes or list(DEFAULT_SCOPES)


def parse_domains(raw: str | None) -> list[str]:
    return parse_list(raw)


def parse_id_token_algs(raw: str | None) -> list[str]:
    values = [item.upper() for item in parse_list(raw)]
    if not values:
        return []
    invalid = [alg for alg in values if alg not in ID_TOKEN_ALG_CHOICES]
    if invalid:
        raise CLIError(
            "id_token_algs must be one of "
            f"{', '.join(ID_TOKEN_ALG_CHOICES)}."
        )
    return values


def normalize_policy(raw: str | None) -> str:
    value = (raw or DEFAULT_AUTO_PROVISION_POLICY).strip().lower()
    if value not in AUTO_PROVISION_POLICIES:
        raise CLIError(
            "auto_provision_policy must be one of "
            f"{', '.join(AUTO_PROVISION_POLICIES)}."
        )
    return value


def normalize_role(raw: str | None) -> str:
    value = (raw or DEFAULT_ROLE).strip().lower()
    if value not in ROLE_CHOICES:
        raise CLIError(f"default_role must be one of {', '.join(ROLE_CHOICES)}.")
    return value


def normalize_scope_mode(raw: str | None) -> str:
    value = (raw or DEFAULT_SCOPE_MODE).strip().lower()
    if value not in SCOPE_MODE_CHOICES:
        raise CLIError(f"scope must be one of {', '.join(SCOPE_MODE_CHOICES)}.")
    return value


def normalize_token_auth_method(raw: str | None) -> str:
    value = (raw or DEFAULT_TOKEN_AUTH_METHOD).strip().lower()
    if value not in TOKEN_AUTH_METHOD_CHOICES:
        raise CLIError(
            "token_auth_method must be one of "
            f"{', '.join(TOKEN_AUTH_METHOD_CHOICES)}."
        )
    return value


def build_config_from_env(
    env: Mapping[str, str],
    *,
    provider_key: str,
    defaults: Mapping[str, str] | None = None,
) -> SsoProviderSeedConfig | None:
    key = provider_key.strip().lower()
    defaults = defaults or {}
    enabled = parse_bool(env.get(env_key(key, "ENABLED")), default=False)
    if not enabled:
        return None

    tenant_scope = normalize_scope_mode(env.get(env_key(key, "SCOPE")))
    tenant_id = (env.get(env_key(key, "TENANT_ID")) or "").strip() or None
    tenant_slug = (env.get(env_key(key, "TENANT_SLUG")) or "").strip() or None

    if tenant_id and tenant_slug:
        raise CLIError("Provide only one of TENANT_ID or TENANT_SLUG for SSO setup.")
    if tenant_scope == "global" and (tenant_id or tenant_slug):
        raise CLIError("SSO scope is global; clear TENANT_ID and TENANT_SLUG.")
    if tenant_scope == "tenant" and not (tenant_id or tenant_slug):
        raise CLIError("SSO tenant scope requires TENANT_ID or TENANT_SLUG.")

    issuer_url = (env.get(env_key(key, "ISSUER_URL")) or defaults.get("issuer_url") or "").strip()
    if not issuer_url:
        raise CLIError("issuer_url is required for SSO setup.")

    client_id = (env.get(env_key(key, "CLIENT_ID")) or "").strip()
    if not client_id:
        raise CLIError("client_id is required for SSO setup.")

    token_auth_method = normalize_token_auth_method(
        env.get(env_key(key, "TOKEN_AUTH_METHOD")) or defaults.get("token_auth_method")
    )

    client_secret: str | None = (env.get(env_key(key, "CLIENT_SECRET")) or "").strip()
    if token_auth_method in {"client_secret_post", "client_secret_basic"} and not client_secret:
        raise CLIError("client_secret is required for the selected token auth method.")
    if not client_secret:
        client_secret = None

    discovery_url = (
        env.get(env_key(key, "DISCOVERY_URL"))
        or defaults.get("discovery_url")
        or ""
    ).strip()
    discovery_value = discovery_url or None

    scopes = parse_scopes(env.get(env_key(key, "SCOPES")) or defaults.get("scopes"))
    pkce_required = parse_bool(
        env.get(env_key(key, "PKCE_REQUIRED")), default=True
    )
    if token_auth_method == "none" and not pkce_required:
        raise CLIError("token_auth_method=none requires PKCE.")
    allowed_id_token_algs = parse_id_token_algs(
        env.get(env_key(key, "ID_TOKEN_ALGS")) or defaults.get("id_token_algs")
    )
    auto_policy = normalize_policy(env.get(env_key(key, "AUTO_PROVISION_POLICY")))
    allowed_domains = parse_domains(env.get(env_key(key, "ALLOWED_DOMAINS")))
    if auto_policy == "domain_allowlist" and not allowed_domains:
        raise CLIError("allowed_domains is required for domain_allowlist policy.")
    default_role = normalize_role(env.get(env_key(key, "DEFAULT_ROLE")))

    return SsoProviderSeedConfig(
        provider_key=key,
        enabled=enabled,
        tenant_scope=tenant_scope,
        tenant_id=tenant_id,
        tenant_slug=tenant_slug,
        issuer_url=issuer_url,
        client_id=client_id,
        client_secret=client_secret,
        discovery_url=discovery_value,
        scopes=scopes,
        pkce_required=pkce_required,
        token_auth_method=token_auth_method,
        allowed_id_token_algs=allowed_id_token_algs,
        auto_provision_policy=auto_policy,
        allowed_domains=allowed_domains,
        default_role=default_role,
    )


__all__ = [
    "SsoProviderSeedConfig",
    "build_config_from_env",
    "env_key",
    "normalize_token_auth_method",
    "normalize_policy",
    "normalize_role",
    "normalize_scope_mode",
    "parse_domains",
    "parse_id_token_algs",
    "parse_scopes",
    "parse_bool",
]
