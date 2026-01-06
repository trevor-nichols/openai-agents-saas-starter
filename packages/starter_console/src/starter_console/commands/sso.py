from __future__ import annotations

import argparse

from starter_console.core import CLIContext, CLIError
from starter_console.services.sso import (
    AUTO_PROVISION_POLICIES,
    CUSTOM_PRESET,
    DEFAULT_AUTO_PROVISION_POLICY,
    DEFAULT_ROLE,
    DEFAULT_SCOPE_MODE,
    DEFAULT_SCOPES,
    DEFAULT_TOKEN_AUTH_METHOD,
    GOOGLE_PROVIDER_KEY,
    ROLE_CHOICES,
    SCOPE_MODE_CHOICES,
    TOKEN_AUTH_METHOD_CHOICES,
    SsoProviderSeedConfig,
    find_preset,
    get_preset,
    list_presets,
    load_env_values,
    normalize_provider_key,
    parse_provider_list,
    preset_defaults,
    resolve_enabled_flag,
    run_sso_setup,
    update_backend_env_providers,
)
from starter_console.services.sso.config import (
    contains_template_placeholders,
    ensure_templates_filled,
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
    preset_choices = [preset.key for preset in list_presets()]
    setup_parser.add_argument(
        "--preset",
        choices=preset_choices,
        default=None,
        help="Preset defaults to prefill issuer/discovery/scopes.",
    )
    setup_parser.add_argument(
        "--provider",
        help="Provider key stored in config/env (default: preset key).",
    )
    setup_parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List available presets and exit.",
    )
    setup_parser.add_argument("--scope", choices=SCOPE_MODE_CHOICES)
    setup_parser.add_argument("--tenant-id")
    setup_parser.add_argument("--tenant-slug")
    setup_parser.add_argument("--issuer-url")
    setup_parser.add_argument("--discovery-url")
    setup_parser.add_argument("--client-id")
    secret_group = setup_parser.add_mutually_exclusive_group()
    secret_group.add_argument("--client-secret")
    secret_group.add_argument(
        "--clear-client-secret",
        action="store_true",
        help="Clear the stored client secret for this provider.",
    )
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


def _render_presets(ctx: CLIContext) -> None:
    ctx.console.info("Available SSO provider presets:", topic="sso")
    for preset in list_presets():
        issuer = preset.issuer_url or "(required)"
        discovery = preset.discovery_url or "(optional)"
        needs_template = (
            contains_template_placeholders(issuer)
            or contains_template_placeholders(discovery)
        )
        template_note = " (replace template placeholders)" if needs_template else ""
        ctx.console.info(
            f"- {preset.key}: {preset.label} — {preset.description}{template_note}",
            topic="sso",
        )
        ctx.console.info(f"  issuer: {issuer}", topic="sso")
        ctx.console.info(f"  discovery: {discovery}", topic="sso")


def handle_sso_setup(args: argparse.Namespace, ctx: CLIContext) -> int:
    if args.list_presets:
        _render_presets(ctx)
        return 0

    env_values = load_env_values(ctx)
    prompt = None
    if not args.non_interactive:
        if ctx.presenter is None:  # pragma: no cover - defensive
            raise CLIError("Presenter not initialized.")
        prompt = ctx.presenter.prompt
    allow_existing = bool(args.from_env or not args.non_interactive)

    preset_key = args.preset
    if preset_key is None and args.provider:
        matched = find_preset(args.provider)
        preset_key = matched.key if matched else CUSTOM_PRESET.key
    preset = get_preset(preset_key or GOOGLE_PROVIDER_KEY)

    if args.provider:
        provider_key = normalize_provider_key(args.provider)
    elif preset.key != "custom":
        provider_key = preset.key
    elif args.non_interactive:
        raise CLIError("provider is required when using the custom preset.")
    else:
        if prompt is None:  # pragma: no cover - defensive
            raise CLIError("Presenter not initialized.")
        provider_key = normalize_provider_key(
            prompt.prompt_string(
                key="SSO_PROVIDER_KEY",
                prompt="Provider key (lowercase, use a-z/0-9/_)",
                default=None,
                required=True,
            )
        )

    defaults = preset_defaults(preset)

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
            if prompt is None:  # pragma: no cover - defensive
                raise CLIError("Presenter not initialized.")
            return prompt.prompt_secret(
                key=key,
                prompt=label,
                existing=default or None,
                required=required and not default,
            )
        if prompt is None:  # pragma: no cover - defensive
            raise CLIError("Presenter not initialized.")
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
        fallback=defaults.get("scope_mode") or DEFAULT_SCOPE_MODE,
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
        fallback=defaults.get("issuer_url"),
        required=True,
    )
    ensure_templates_filled(issuer_url, label="Issuer URL", provider_key=provider_key)

    discovery_url = _resolve_string(
        key=env_key(provider_key, "DISCOVERY_URL"),
        label="OIDC discovery URL",
        provided=args.discovery_url,
        existing=env_values.get(env_key(provider_key, "DISCOVERY_URL")),
        fallback=defaults.get("discovery_url"),
        required=False,
    )
    ensure_templates_filled(
        discovery_url,
        label="Discovery URL",
        provider_key=provider_key,
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
        fallback=defaults.get("token_auth_method") or DEFAULT_TOKEN_AUTH_METHOD,
        required=True,
    )
    token_auth_method = normalize_token_auth_method(token_auth_method_raw)
    secret_required = token_auth_method in {"client_secret_basic", "client_secret_post"}
    clear_client_secret = bool(args.clear_client_secret)
    if clear_client_secret and secret_required:
        raise CLIError(
            "Cannot clear the client secret for client_secret_basic/post. "
            "Provide a new secret or change the token auth method."
        )
    if clear_client_secret:
        client_secret = None
    else:
        client_secret = _resolve_string(
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
        fallback=defaults.get("scopes") or ",".join(DEFAULT_SCOPES),
        required=True,
    )
    scopes = parse_scopes(scopes_raw)

    pkce_required = (
        args.pkce_required if args.pkce_required is not None else preset.pkce_required
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
        fallback=defaults.get("auto_provision_policy") or DEFAULT_AUTO_PROVISION_POLICY,
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
        fallback=defaults.get("default_role") or DEFAULT_ROLE,
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
        clear_client_secret=clear_client_secret,
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
    env_values = load_env_values(ctx)

    provider_list = parse_provider_list(env_values.get("SSO_PROVIDERS"))
    if config.enabled:
        if provider_key not in provider_list:
            provider_list.append(provider_key)
    else:
        provider_list = [item for item in provider_list if item != provider_key]
    update_backend_env_providers(ctx.project_root, provider_list)
    ctx.console.success("Updated SSO_PROVIDERS.", topic="sso")
    ctx.console.success("SSO setup complete.", topic="sso")
    return 0


__all__ = ["register"]
