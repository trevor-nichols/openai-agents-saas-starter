from __future__ import annotations

import argparse

from starter_console.core import CLIContext, CLIError
from starter_console.services.sso import (
    AUTO_PROVISION_POLICIES,
    DEFAULT_AUTO_PROVISION_POLICY,
    DEFAULT_ROLE,
    DEFAULT_SCOPE_MODE,
    DEFAULT_SCOPES,
    DEFAULT_TOKEN_AUTH_METHOD,
    GOOGLE_DISCOVERY_URL,
    GOOGLE_ISSUER_URL,
    GOOGLE_PROVIDER_KEY,
    ROLE_CHOICES,
    SCOPE_MODE_CHOICES,
    TOKEN_AUTH_METHOD_CHOICES,
    SsoProviderSeedConfig,
    load_env_values,
    resolve_default_config,
    resolve_enabled_flag,
    run_sso_setup,
)
from starter_console.services.sso.config import (
    env_key,
    normalize_policy,
    normalize_role,
    normalize_scope_mode,
    normalize_token_auth_method,
    parse_domains,
    parse_id_token_algs,
    parse_scopes,
)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    sso_parser = subparsers.add_parser("sso", help="SSO provisioning helpers.")
    sso_subparsers = sso_parser.add_subparsers(dest="sso_command")

    setup_parser = sso_subparsers.add_parser(
        "setup",
        help="Seed an OIDC SSO provider config.",
    )
    setup_parser.add_argument(
        "--provider",
        default=GOOGLE_PROVIDER_KEY,
        choices=[GOOGLE_PROVIDER_KEY],
    )
    setup_parser.add_argument("--scope", choices=SCOPE_MODE_CHOICES)
    setup_parser.add_argument("--tenant-id")
    setup_parser.add_argument("--tenant-slug")
    setup_parser.add_argument("--issuer-url")
    setup_parser.add_argument("--discovery-url")
    setup_parser.add_argument("--client-id")
    setup_parser.add_argument("--client-secret")
    setup_parser.add_argument("--scopes")
    setup_parser.add_argument(
        "--token-auth-method",
        choices=TOKEN_AUTH_METHOD_CHOICES,
    )
    setup_parser.add_argument(
        "--id-token-algs",
        help="Comma-separated list of allowed ID token signing algorithms",
    )
    setup_parser.add_argument("--allowed-domains")
    setup_parser.add_argument(
        "--auto-provision-policy",
        choices=AUTO_PROVISION_POLICIES,
    )
    setup_parser.add_argument("--default-role", choices=ROLE_CHOICES)

    enabled_group = setup_parser.add_mutually_exclusive_group()
    enabled_group.add_argument("--enable", dest="enabled", action="store_true")
    enabled_group.add_argument("--disable", dest="enabled", action="store_false")

    pkce_group = setup_parser.add_mutually_exclusive_group()
    pkce_group.add_argument("--pkce-required", dest="pkce_required", action="store_true")
    pkce_group.add_argument("--no-pkce", dest="pkce_required", action="store_false")

    setup_parser.add_argument(
        "--from-env",
        action="store_true",
        help="Use existing SSO_* env values as defaults.",
    )
    setup_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable prompts; requires required values via flags or env.",
    )
    setup_parser.set_defaults(handler=handle_sso_setup)


def handle_sso_setup(args: argparse.Namespace, ctx: CLIContext) -> int:
    provider_key = (args.provider or GOOGLE_PROVIDER_KEY).strip().lower()
    defaults = resolve_default_config(provider_key)
    env_values = load_env_values(ctx)
    if ctx.presenter is None:  # pragma: no cover - defensive
        raise CLIError("Presenter not initialized.")
    prompt = ctx.presenter.prompt
    allow_existing = bool(args.from_env or not args.non_interactive)

    def _resolve_string(
        *,
        key: str,
        label: str,
        provided: str | None,
        existing: str | None,
        fallback: str | None,
        required: bool,
        secret: bool = False,
    ) -> str:
        if provided is not None and str(provided).strip():
            return str(provided).strip()
        default = (existing if allow_existing else None) or fallback or ""
        if args.non_interactive:
            if required and not default:
                raise CLIError(f"{label} is required for SSO setup.")
            return default
        if secret:
            return prompt.prompt_secret(
                key=key,
                prompt=label,
                existing=default or None,
                required=required and not default,
            )
        return prompt.prompt_string(
            key=key,
            prompt=label,
            default=default or None,
            required=required,
        )

    enabled = resolve_enabled_flag(
        provided=args.enabled,
        existing=env_values.get(env_key(provider_key, "ENABLED")),
    )

    scope_value = _resolve_string(
        key=env_key(provider_key, "SCOPE"),
        label="SSO config scope (global or tenant)",
        provided=args.scope,
        existing=env_values.get(env_key(provider_key, "SCOPE")),
        fallback=DEFAULT_SCOPE_MODE,
        required=True,
    )
    tenant_scope = normalize_scope_mode(scope_value)

    tenant_id = _resolve_string(
        key=env_key(provider_key, "TENANT_ID"),
        label="Tenant ID (UUID)",
        provided=args.tenant_id,
        existing=env_values.get(env_key(provider_key, "TENANT_ID")),
        fallback=None,
        required=False,
    )
    tenant_slug = _resolve_string(
        key=env_key(provider_key, "TENANT_SLUG"),
        label="Tenant slug",
        provided=args.tenant_slug,
        existing=env_values.get(env_key(provider_key, "TENANT_SLUG")),
        fallback=None,
        required=False,
    )

    if tenant_scope == "tenant" and tenant_id and tenant_slug:
        raise CLIError("Provide only one of tenant-id or tenant-slug.")
    if tenant_scope == "tenant" and not (tenant_id or tenant_slug):
        if args.non_interactive:
            raise CLIError("Tenant scope requires --tenant-id or --tenant-slug.")
        tenant_slug = _resolve_string(
            key=env_key(provider_key, "TENANT_SLUG"),
            label="Tenant slug",
            provided=None,
            existing=tenant_slug or None,
            fallback=None,
            required=True,
        )
    if tenant_scope == "global":
        tenant_id = ""
        tenant_slug = ""

    issuer_url = _resolve_string(
        key=env_key(provider_key, "ISSUER_URL"),
        label="OIDC issuer URL",
        provided=args.issuer_url,
        existing=env_values.get(env_key(provider_key, "ISSUER_URL")),
        fallback=GOOGLE_ISSUER_URL,
        required=True,
    )
    discovery_url = _resolve_string(
        key=env_key(provider_key, "DISCOVERY_URL"),
        label="OIDC discovery URL",
        provided=args.discovery_url,
        existing=env_values.get(env_key(provider_key, "DISCOVERY_URL")),
        fallback=GOOGLE_DISCOVERY_URL,
        required=False,
    )
    client_id = _resolve_string(
        key=env_key(provider_key, "CLIENT_ID"),
        label="OIDC client ID",
        provided=args.client_id,
        existing=env_values.get(env_key(provider_key, "CLIENT_ID")),
        fallback=None,
        required=True,
    )
    token_auth_method_raw = _resolve_string(
        key=env_key(provider_key, "TOKEN_AUTH_METHOD"),
        label="Token endpoint auth method",
        provided=args.token_auth_method,
        existing=env_values.get(env_key(provider_key, "TOKEN_AUTH_METHOD")),
        fallback=DEFAULT_TOKEN_AUTH_METHOD,
        required=True,
    )
    token_auth_method = normalize_token_auth_method(token_auth_method_raw)
    secret_required = token_auth_method in {"client_secret_basic", "client_secret_post"}
    client_secret: str | None = _resolve_string(
        key=env_key(provider_key, "CLIENT_SECRET"),
        label="OIDC client secret",
        provided=args.client_secret,
        existing=env_values.get(env_key(provider_key, "CLIENT_SECRET")),
        fallback=None,
        required=secret_required,
        secret=True,
    )
    if secret_required and not client_secret:
        raise CLIError("OIDC client secret is required for the selected auth method.")
    if not client_secret:
        client_secret = None

    scopes_raw = _resolve_string(
        key=env_key(provider_key, "SCOPES"),
        label="OIDC scopes (comma-separated)",
        provided=args.scopes,
        existing=env_values.get(env_key(provider_key, "SCOPES")),
        fallback=",".join(DEFAULT_SCOPES),
        required=True,
    )
    scopes = parse_scopes(scopes_raw)

    pkce_required = (
        args.pkce_required
        if args.pkce_required is not None
        else defaults.pkce_required
    )
    if token_auth_method == "none" and not pkce_required:
        raise CLIError("token_auth_method=none requires PKCE.")

    id_token_algs_raw = _resolve_string(
        key=env_key(provider_key, "ID_TOKEN_ALGS"),
        label=(
            "Allowed ID token algorithms (comma-separated, blank to use discovery)"
        ),
        provided=args.id_token_algs,
        existing=env_values.get(env_key(provider_key, "ID_TOKEN_ALGS")),
        fallback="",
        required=False,
    )
    allowed_id_token_algs = parse_id_token_algs(id_token_algs_raw)

    auto_policy_raw = _resolve_string(
        key=env_key(provider_key, "AUTO_PROVISION_POLICY"),
        label="Auto-provision policy",
        provided=args.auto_provision_policy,
        existing=env_values.get(env_key(provider_key, "AUTO_PROVISION_POLICY")),
        fallback=DEFAULT_AUTO_PROVISION_POLICY,
        required=True,
    )
    auto_policy = normalize_policy(auto_policy_raw)

    allowed_domains_raw = _resolve_string(
        key=env_key(provider_key, "ALLOWED_DOMAINS"),
        label="Allowed email domains (comma-separated)",
        provided=args.allowed_domains,
        existing=env_values.get(env_key(provider_key, "ALLOWED_DOMAINS")),
        fallback="",
        required=False,
    )
    allowed_domains = parse_domains(allowed_domains_raw)
    if auto_policy == "domain_allowlist" and not allowed_domains:
        raise CLIError("allowed-domains is required for domain_allowlist policy.")

    default_role_raw = _resolve_string(
        key=env_key(provider_key, "DEFAULT_ROLE"),
        label="Default role for auto-provision",
        provided=args.default_role,
        existing=env_values.get(env_key(provider_key, "DEFAULT_ROLE")),
        fallback=DEFAULT_ROLE,
        required=True,
    )
    default_role = normalize_role(default_role_raw)

    config = SsoProviderSeedConfig(
        provider_key=provider_key,
        enabled=enabled,
        tenant_scope=tenant_scope,
        tenant_id=tenant_id or None,
        tenant_slug=tenant_slug or None,
        issuer_url=issuer_url,
        client_id=client_id,
        client_secret=client_secret,
        discovery_url=discovery_url or None,
        scopes=scopes,
        pkce_required=pkce_required,
        token_auth_method=token_auth_method,
        allowed_id_token_algs=allowed_id_token_algs,
        auto_provision_policy=auto_policy,
        allowed_domains=allowed_domains,
        default_role=default_role,
    )

    run_sso_setup(ctx, config=config, update_env=True)
    ctx.console.success("SSO setup complete.", topic="sso")
    return 0


__all__ = ["register"]
