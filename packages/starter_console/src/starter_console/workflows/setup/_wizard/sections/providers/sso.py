from __future__ import annotations

from starter_console.core import CLIError
from starter_console.services.sso.config import (
    ensure_templates_filled,
    env_key,
    normalize_policy,
    normalize_provider_key,
    normalize_role,
    normalize_token_auth_method,
    parse_domains,
    parse_id_token_algs,
    parse_provider_list,
    parse_scopes,
)
from starter_console.services.sso.constants import (
    AUTO_PROVISION_POLICIES,
    DEFAULT_AUTO_PROVISION_POLICY,
    DEFAULT_ROLE,
    DEFAULT_SCOPE_MODE,
    DEFAULT_SCOPES,
    DEFAULT_TOKEN_AUTH_METHOD,
    ROLE_CHOICES,
    SCOPE_MODE_CHOICES,
    TOKEN_AUTH_METHOD_CHOICES,
)
from starter_console.services.sso.registry import (
    CUSTOM_PRESET,
    find_preset,
    get_preset,
    is_custom_preset,
    list_presets,
    preset_defaults,
)

from ....inputs import InputProvider
from ...context import WizardContext


def collect_sso(context: WizardContext, provider: InputProvider) -> None:
    if context.is_headless:
        _collect_sso_headless(context, provider)
    else:
        _collect_sso_interactive(context, provider)


def _set_sso_providers(context: WizardContext, providers: list[str]) -> None:
    context.set_backend("SSO_PROVIDERS", ",".join(providers))


def _collect_sso_provider(
    context: WizardContext,
    provider: InputProvider,
    *,
    preset_key: str,
    provider_key: str,
    prompt_enabled: bool,
    enabled_default: bool,
) -> bool:
    preset = get_preset(preset_key)
    normalized_key = normalize_provider_key(provider_key)
    label = preset.label if not is_custom_preset(preset) else normalized_key
    defaults = preset_defaults(preset)

    enabled_key = env_key(normalized_key, "ENABLED")
    if prompt_enabled:
        enabled = provider.prompt_bool(
            key=enabled_key,
            prompt=f"Enable {label} SSO (OIDC)?",
            default=context.current_bool(enabled_key, enabled_default),
        )
    else:
        enabled = enabled_default
    context.set_backend_bool(enabled_key, enabled)
    if not enabled:
        context.console.info(f"{label} SSO disabled.", topic="sso")
        return False

    app_public_url = (context.current("APP_PUBLIC_URL") or "").strip().rstrip("/")
    if app_public_url:
        redirect_uri = f"{app_public_url}/auth/sso/{normalized_key}/callback"
        context.console.info(f"Register redirect URI: {redirect_uri}", topic="sso")

    scope_key = env_key(normalized_key, "SCOPE")
    scope_mode = provider.prompt_choice(
        key=scope_key,
        prompt="SSO config scope",
        choices=SCOPE_MODE_CHOICES,
        default=context.current(scope_key) or defaults.get("scope_mode") or DEFAULT_SCOPE_MODE,
    ).strip()
    context.set_backend(scope_key, scope_mode)

    tenant_slug_key = env_key(normalized_key, "TENANT_SLUG")
    tenant_id_key = env_key(normalized_key, "TENANT_ID")
    if scope_mode == "tenant":
        tenant_slug = provider.prompt_string(
            key=tenant_slug_key,
            prompt="Tenant slug for SSO config (leave blank to use tenant ID)",
            default=context.current(tenant_slug_key) or context.current("TENANT_DEFAULT_SLUG"),
            required=False,
        ).strip()
        tenant_id = ""
        if not tenant_slug:
            tenant_id = provider.prompt_string(
                key=tenant_id_key,
                prompt="Tenant ID (UUID) for SSO config",
                default=context.current(tenant_id_key) or "",
                required=True,
            ).strip()
            if not tenant_id:
                raise CLIError("Tenant ID is required when scope=tenant.")
        context.set_backend(tenant_slug_key, tenant_slug)
        context.set_backend(tenant_id_key, tenant_id)
    else:
        context.set_backend(tenant_slug_key, "")
        context.set_backend(tenant_id_key, "")

    issuer_key = env_key(normalized_key, "ISSUER_URL")
    issuer_url = provider.prompt_string(
        key=issuer_key,
        prompt="OIDC issuer URL",
        default=context.current(issuer_key) or defaults.get("issuer_url") or "",
        required=True,
    ).strip()
    if not issuer_url:
        raise CLIError("OIDC issuer URL is required.")
    ensure_templates_filled(issuer_url, label="Issuer URL", provider_key=normalized_key)
    context.set_backend(issuer_key, issuer_url)

    discovery_key = env_key(normalized_key, "DISCOVERY_URL")
    discovery_url = provider.prompt_string(
        key=discovery_key,
        prompt="OIDC discovery URL (blank = issuer/.well-known)",
        default=context.current(discovery_key) or defaults.get("discovery_url") or "",
        required=False,
    ).strip()
    ensure_templates_filled(
        discovery_url,
        label="Discovery URL",
        provider_key=normalized_key,
    )
    context.set_backend(discovery_key, discovery_url)

    client_id_key = env_key(normalized_key, "CLIENT_ID")
    client_id_label = f"{label} client ID" if label else "OIDC client ID"
    client_id = provider.prompt_string(
        key=client_id_key,
        prompt=client_id_label,
        default=context.current(client_id_key) or "",
        required=True,
    ).strip()
    if not client_id:
        raise CLIError("OIDC client ID is required.")
    context.set_backend(client_id_key, client_id)

    token_auth_key = env_key(normalized_key, "TOKEN_AUTH_METHOD")
    id_token_algs_key = env_key(normalized_key, "ID_TOKEN_ALGS")
    has_existing_advanced = bool(
        (context.current(token_auth_key) or "").strip()
        or (context.current(id_token_algs_key) or "").strip()
    )
    use_advanced = provider.prompt_bool(
        key=f"SSO_{normalized_key.upper()}_ADVANCED_SETTINGS",
        prompt="Configure advanced SSO settings (token auth method, ID token algs)?",
        default=has_existing_advanced,
    )
    if use_advanced:
        token_auth_raw = provider.prompt_choice(
            key=token_auth_key,
            prompt="Token endpoint auth method",
            choices=TOKEN_AUTH_METHOD_CHOICES,
            default=context.current(token_auth_key)
            or defaults.get("token_auth_method")
            or DEFAULT_TOKEN_AUTH_METHOD,
        )
        token_auth_method = normalize_token_auth_method(token_auth_raw)
        id_token_algs_raw = provider.prompt_string(
            key=id_token_algs_key,
            prompt="Allowed ID token algorithms (comma-separated, blank = discovery)",
            default=context.current(id_token_algs_key) or "",
            required=False,
        )
        allowed_id_token_algs = parse_id_token_algs(id_token_algs_raw)
    else:
        token_auth_method = normalize_token_auth_method(
            context.current(token_auth_key)
            or defaults.get("token_auth_method")
            or DEFAULT_TOKEN_AUTH_METHOD
        )
        allowed_id_token_algs = parse_id_token_algs(context.current(id_token_algs_key) or "")

    context.set_backend(token_auth_key, token_auth_method)
    context.set_backend(id_token_algs_key, ",".join(allowed_id_token_algs))

    client_secret_key = env_key(normalized_key, "CLIENT_SECRET")
    client_secret_required = token_auth_method in {"client_secret_basic", "client_secret_post"}
    client_secret = provider.prompt_secret(
        key=client_secret_key,
        prompt=f"{label} client secret",
        existing=context.current(client_secret_key),
        required=client_secret_required,
    )
    if client_secret_required and not client_secret:
        raise CLIError("OIDC client secret is required.")
    context.set_backend(client_secret_key, client_secret, mask=True)

    scopes_key = env_key(normalized_key, "SCOPES")
    scopes_raw = provider.prompt_string(
        key=scopes_key,
        prompt="OIDC scopes (comma-separated)",
        default=context.current(scopes_key)
        or defaults.get("scopes")
        or ",".join(DEFAULT_SCOPES),
        required=True,
    )
    scopes = parse_scopes(scopes_raw)
    context.set_backend(scopes_key, ",".join(scopes))

    pkce_key = env_key(normalized_key, "PKCE_REQUIRED")
    pkce_required = provider.prompt_bool(
        key=pkce_key,
        prompt="Require PKCE (recommended)?",
        default=context.current_bool(pkce_key, preset.pkce_required),
    )
    if token_auth_method == "none" and not pkce_required:
        raise CLIError("Token auth method 'none' requires PKCE.")
    context.set_backend_bool(pkce_key, pkce_required)

    policy_key = env_key(normalized_key, "AUTO_PROVISION_POLICY")
    policy_raw = provider.prompt_choice(
        key=policy_key,
        prompt="SSO auto-provision policy",
        choices=AUTO_PROVISION_POLICIES,
        default=context.current(policy_key)
        or defaults.get("auto_provision_policy")
        or DEFAULT_AUTO_PROVISION_POLICY,
    )
    policy = normalize_policy(policy_raw)
    context.set_backend(policy_key, policy)

    allowed_domains_key = env_key(normalized_key, "ALLOWED_DOMAINS")
    default_role_key = env_key(normalized_key, "DEFAULT_ROLE")
    if policy == "domain_allowlist":
        allowed_raw = provider.prompt_string(
            key=allowed_domains_key,
            prompt="Allowed email domains (comma-separated)",
            default=context.current(allowed_domains_key) or "",
            required=True,
        )
        domains = parse_domains(allowed_raw)
        if not domains:
            raise CLIError("At least one domain is required for domain allowlist policy.")
        context.set_backend(allowed_domains_key, ",".join(domains))

        role_raw = provider.prompt_choice(
            key=default_role_key,
            prompt="Default role for auto-provisioned users",
            choices=ROLE_CHOICES,
            default=context.current(default_role_key)
            or defaults.get("default_role")
            or DEFAULT_ROLE,
        )
        role = normalize_role(role_raw)
        context.set_backend(default_role_key, role)
    else:
        context.set_backend(allowed_domains_key, "")
        context.set_backend(
            default_role_key,
            context.current(default_role_key) or defaults.get("default_role") or DEFAULT_ROLE,
        )

    return True


def _collect_sso_headless(context: WizardContext, provider: InputProvider) -> None:
    providers_raw = provider.prompt_string(
        key="SSO_PROVIDERS",
        prompt="SSO providers (comma-separated)",
        default=context.current("SSO_PROVIDERS") or "",
        required=False,
    )
    provider_keys = parse_provider_list(providers_raw)

    if not provider_keys:
        for preset in list_presets():
            if is_custom_preset(preset):
                continue
            enabled_key = env_key(preset.key, "ENABLED")
            enabled = provider.prompt_bool(
                key=enabled_key,
                prompt=f"Enable {preset.label} SSO (OIDC)?",
                default=context.current_bool(enabled_key, False),
            )
            if enabled:
                provider_keys.append(preset.key)

    if not provider_keys:
        context.console.info("SSO not enabled.", topic="sso")
        _set_sso_providers(context, [])
        return

    enabled_providers: list[str] = []
    for key in provider_keys:
        preset = find_preset(key) or CUSTOM_PRESET
        configured = _collect_sso_provider(
            context,
            provider,
            preset_key=preset.key,
            provider_key=key,
            prompt_enabled=False,
            enabled_default=True,
        )
        if configured:
            enabled_providers.append(normalize_provider_key(key))

    _set_sso_providers(context, enabled_providers)


def _collect_sso_interactive(context: WizardContext, provider: InputProvider) -> None:
    configure = provider.prompt_bool(
        key="SSO_CONFIGURE",
        prompt="Configure OIDC SSO providers now?",
        default=bool(context.current("SSO_PROVIDERS")),
    )
    if not configure:
        if context.current("SSO_PROVIDERS") is None:
            _set_sso_providers(context, [])
        context.console.info("Skipping SSO configuration.", topic="sso")
        return

    preset_choices = [preset.key for preset in list_presets()]
    enabled_providers: list[str] = []
    while True:
        preset_key = provider.prompt_choice(
            key="SSO_PROVIDER_PRESET",
            prompt="Choose an SSO provider preset",
            choices=preset_choices,
            default=preset_choices[0],
        ).strip()
        preset = get_preset(preset_key)
        provider_key = preset.key
        if is_custom_preset(preset):
            provider_key = normalize_provider_key(
                provider.prompt_string(
                    key="SSO_CUSTOM_PROVIDER_KEY",
                    prompt="Provider key (lowercase, use a-z/0-9/_)",
                    default="",
                    required=True,
                )
            )

        if provider_key in enabled_providers:
            context.console.warn(
                f"Provider '{provider_key}' already configured; choose another.",
                topic="sso",
            )
        else:
            configured = _collect_sso_provider(
                context,
                provider,
                preset_key=preset.key,
                provider_key=provider_key,
                prompt_enabled=False,
                enabled_default=True,
            )
            if configured:
                enabled_providers.append(provider_key)

        add_more = provider.prompt_bool(
            key="SSO_ADD_PROVIDER",
            prompt="Add another SSO provider?",
            default=False,
        )
        if not add_more:
            break

    _set_sso_providers(context, enabled_providers)


__all__ = ["collect_sso"]
