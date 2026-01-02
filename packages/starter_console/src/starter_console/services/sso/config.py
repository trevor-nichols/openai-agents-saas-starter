from __future__ import annotations

import json
import re
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

_PROVIDER_KEY_RE = re.compile(r"^[a-z0-9_]+$")
_TEMPLATE_RE = re.compile(r"{[a-zA-Z0-9_]+}")
_RESERVED_PROVIDER_KEYS = {"custom"}


def normalize_provider_key(raw: str, *, allow_reserved: bool = False) -> str:
    value = raw.strip().lower()
    if not value:
        raise CLIError("provider_key is required.")
    if not _PROVIDER_KEY_RE.match(value):
        raise CLIError("provider_key must match [a-z0-9_]+.")
    if not allow_reserved and value in _RESERVED_PROVIDER_KEYS:
        raise CLIError(
            f"provider_key '{value}' is reserved for presets; choose another key."
        )
    return value


def contains_template_placeholders(value: str | None) -> bool:
    if not value:
        return False
    return bool(_TEMPLATE_RE.search(value))


def ensure_templates_filled(
    value: str | None,
    *,
    label: str,
    provider_key: str | None = None,
) -> None:
    if not contains_template_placeholders(value):
        return
    suffix = f" for provider '{provider_key}'" if provider_key else ""
    raise CLIError(
        f"{label}{suffix} contains template placeholders; replace them first."
    )


def env_key(provider_key: str, suffix: str) -> str:
    normalized = normalize_provider_key(provider_key)
    return f"SSO_{normalized.upper()}_{suffix}"


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
    clear_client_secret: bool = False

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
        if self.clear_client_secret:
            args.append("--clear-client-secret")
        elif self.client_secret:
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


def parse_provider_list(raw: str | None) -> list[str]:
    providers = [normalize_provider_key(item) for item in parse_list(raw)]
    seen: set[str] = set()
    ordered: list[str] = []
    for provider in providers:
        if provider in seen:
            continue
        seen.add(provider)
        ordered.append(provider)
    return ordered


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


def resolve_enabled_providers(env: Mapping[str, str]) -> list[str]:
    if "SSO_PROVIDERS" not in env:
        raise CLIError(
            "SSO_PROVIDERS must be set (use an empty value to disable all providers)."
        )
    return parse_provider_list(env.get("SSO_PROVIDERS"))


def build_config_from_env(
    env: Mapping[str, str],
    *,
    provider_key: str,
    defaults: Mapping[str, str] | None = None,
    enabled_default: bool | None = None,
    enforce_enabled_flag: bool = False,
) -> SsoProviderSeedConfig | None:
    key = normalize_provider_key(provider_key)
    defaults = defaults or {}
    if enforce_enabled_flag:
        enabled = parse_bool(
            env.get(env_key(key, "ENABLED")),
            default=bool(enabled_default) if enabled_default is not None else False,
        )
    else:
        enabled = bool(enabled_default) if enabled_default is not None else True
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

    issuer_url = (
        env.get(env_key(key, "ISSUER_URL"))
        or defaults.get("issuer_url")
        or ""
    ).strip()
    if not issuer_url:
        raise CLIError("issuer_url is required for SSO setup.")
    ensure_templates_filled(issuer_url, label="Issuer URL", provider_key=key)

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
    ensure_templates_filled(discovery_url, label="Discovery URL", provider_key=key)
    discovery_value = discovery_url or None

    scopes = parse_scopes(env.get(env_key(key, "SCOPES")) or defaults.get("scopes"))
    pkce_default_raw = defaults.get("pkce_required")
    pkce_default = (
        parse_bool(str(pkce_default_raw), default=True)
        if pkce_default_raw is not None
        else True
    )
    pkce_required = parse_bool(
        env.get(env_key(key, "PKCE_REQUIRED")), default=pkce_default
    )
    if token_auth_method == "none" and not pkce_required:
        raise CLIError("token_auth_method=none requires PKCE.")
    allowed_id_token_algs = parse_id_token_algs(
        env.get(env_key(key, "ID_TOKEN_ALGS")) or defaults.get("id_token_algs")
    )
    auto_policy = normalize_policy(
        env.get(env_key(key, "AUTO_PROVISION_POLICY"))
        or defaults.get("auto_provision_policy")
    )
    allowed_domains = parse_domains(env.get(env_key(key, "ALLOWED_DOMAINS")))
    if auto_policy == "domain_allowlist" and not allowed_domains:
        raise CLIError("allowed_domains is required for domain_allowlist policy.")
    default_role = normalize_role(
        env.get(env_key(key, "DEFAULT_ROLE")) or defaults.get("default_role")
    )

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
    "contains_template_placeholders",
    "ensure_templates_filled",
    "env_key",
    "normalize_provider_key",
    "normalize_token_auth_method",
    "normalize_policy",
    "normalize_role",
    "normalize_scope_mode",
    "parse_provider_list",
    "parse_domains",
    "parse_id_token_algs",
    "parse_scopes",
    "parse_bool",
    "resolve_enabled_providers",
]
