from __future__ import annotations

import json
import os
import subprocess
from urllib.parse import quote, urlparse

from redis import Redis

from starter_console.adapters.stripe_cli import StripeCli
from starter_console.core import CLIError
from starter_console.services.sso.config import (
    env_key,
    normalize_policy,
    normalize_role,
    normalize_token_auth_method,
    parse_domains,
    parse_id_token_algs,
    parse_scopes,
)
from starter_console.services.sso.constants import (
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
)
from starter_console.workflows.stripe.cli_helpers import ensure_stripe_cli

from ...automation import AutomationPhase, AutomationStatus
from ...inputs import InputProvider
from ...validators import validate_plan_map, validate_redis_url
from ..context import WizardContext

_LOCAL_DB_MODE_KEY = "STARTER_LOCAL_DATABASE_MODE"
_LOCAL_DB_MODES = ("compose", "external")


def run(context: WizardContext, provider: InputProvider) -> None:
    context.console.section(
        "Infra & Providers",
        "Wire up databases, AI providers, Redis, billing, and email transports.",
    )
    collect_database(context, provider)
    _collect_ai_providers(context, provider)
    _collect_redis(context, provider)
    _collect_billing(context, provider)
    _collect_email(context, provider)
    _collect_sso(context, provider)
    _maybe_run_migrations(context, provider)


def collect_database(context: WizardContext, provider: InputProvider) -> None:
    if context.profile == "demo":
        _collect_local_database(context, provider)
        return

    db_url = provider.prompt_string(
        key="DATABASE_URL",
        prompt="Primary Postgres connection URL (DATABASE_URL)",
        default=context.current("DATABASE_URL") or os.getenv("DATABASE_URL"),
        required=True,
    ).strip()
    if not db_url:
        raise CLIError("DATABASE_URL is required outside demo profiles.")
    context.set_backend("DATABASE_URL", db_url)


def _collect_local_database(context: WizardContext, provider: InputProvider) -> None:
    existing_url = (context.current("DATABASE_URL") or os.getenv("DATABASE_URL") or "").strip()
    existing_mode = (context.current(_LOCAL_DB_MODE_KEY) or "").strip().lower()
    if existing_mode not in _LOCAL_DB_MODES:
        existing_mode = _infer_local_db_mode(existing_url)

    mode = provider.prompt_choice(
        key=_LOCAL_DB_MODE_KEY,
        prompt="Local database mode",
        choices=_LOCAL_DB_MODES,
        default=existing_mode or "compose",
    ).strip()
    if mode not in _LOCAL_DB_MODES:  # pragma: no cover - provider enforces choices
        raise CLIError(f"{_LOCAL_DB_MODE_KEY} must be one of {', '.join(_LOCAL_DB_MODES)}.")

    context.set_backend(_LOCAL_DB_MODE_KEY, mode)
    if mode == "external":
        db_url = provider.prompt_string(
            key="DATABASE_URL",
            prompt="Primary Postgres connection URL (DATABASE_URL)",
            default=existing_url or None,
            required=True,
        ).strip()
        if not db_url:
            raise CLIError("DATABASE_URL is required when STARTER_LOCAL_DATABASE_MODE=external.")
        context.set_backend("DATABASE_URL", db_url)
        return

    # STARTER_LOCAL_DATABASE_MODE=compose: manage Docker Postgres inputs and derive DATABASE_URL.
    port = _prompt_port(
        context,
        provider,
        key="POSTGRES_PORT",
        prompt="Local Postgres port (host)",
        default=context.current("POSTGRES_PORT") or "5432",
    )
    user = _prompt_nonempty(
        provider,
        key="POSTGRES_USER",
        prompt="Local Postgres username",
        default=context.current("POSTGRES_USER") or "postgres",
    )
    password = provider.prompt_secret(
        key="POSTGRES_PASSWORD",
        prompt="Local Postgres password",
        existing=context.current("POSTGRES_PASSWORD") or "postgres",
        required=True,
    )
    db_name = _prompt_nonempty(
        provider,
        key="POSTGRES_DB",
        prompt="Local Postgres database name",
        default=context.current("POSTGRES_DB") or "saas_starter_db",
    )

    context.set_backend("POSTGRES_PORT", str(port))
    context.set_backend("POSTGRES_USER", user)
    context.set_backend("POSTGRES_PASSWORD", password, mask=True)
    context.set_backend("POSTGRES_DB", db_name)

    derived = _build_local_postgres_url(
        username=user,
        password=password,
        host="localhost",
        port=port,
        database=db_name,
    )
    context.set_backend("DATABASE_URL", derived)


def _infer_local_db_mode(existing_url: str) -> str:
    if not existing_url:
        return "compose"
    try:
        parsed = urlparse(existing_url)
    except ValueError:
        return "compose"
    host = (parsed.hostname or "").strip().lower()
    if host and host not in {"localhost", "127.0.0.1"}:
        return "external"
    return "compose"


def _prompt_nonempty(provider: InputProvider, *, key: str, prompt: str, default: str) -> str:
    value = provider.prompt_string(key=key, prompt=prompt, default=default, required=True).strip()
    if not value:
        raise CLIError(f"{key} cannot be blank.")
    return value


def _prompt_port(
    context: WizardContext,
    provider: InputProvider,
    *,
    key: str,
    prompt: str,
    default: str,
) -> int:
    raw = provider.prompt_string(key=key, prompt=prompt, default=default, required=True).strip()
    try:
        port = int(raw)
    except ValueError as exc:
        raise CLIError(f"{key} must be an integer.") from exc
    if not (1 <= port <= 65535):
        raise CLIError(f"{key} must be between 1 and 65535.")
    return port


def _build_local_postgres_url(
    *,
    username: str,
    password: str,
    host: str,
    port: int,
    database: str,
) -> str:
    user_enc = quote(username, safe="")
    pass_enc = quote(password, safe="")
    db_enc = quote(database, safe="")
    return f"postgresql+asyncpg://{user_enc}:{pass_enc}@{host}:{port}/{db_enc}"


def _collect_ai_providers(context: WizardContext, provider: InputProvider) -> None:
    openai_key = provider.prompt_secret(
        key="OPENAI_API_KEY",
        prompt="OpenAI API key (required)",
        existing=context.current("OPENAI_API_KEY"),
        required=True,
    )
    context.set_backend("OPENAI_API_KEY", openai_key, mask=True)

    for key, label in (
        ("ANTHROPIC_API_KEY", "Anthropic API key"),
        ("GEMINI_API_KEY", "Google Gemini API key"),
        ("XAI_API_KEY", "xAI API key"),
    ):
        default_enabled = bool(context.current(key))
        if provider.prompt_bool(
            key=f"ENABLE_{key}",
            prompt=f"Configure {label}?",
            default=default_enabled,
        ):
            value = provider.prompt_secret(
                key=key,
                prompt=label,
                existing=context.current(key),
                required=False,
            )
            if value:
                context.set_backend(key, value, mask=True)
            else:
                context.set_backend(key, "")
        else:
            context.set_backend(key, "")

def _collect_redis(context: WizardContext, provider: InputProvider) -> None:
    primary = provider.prompt_string(
        key="REDIS_URL",
        prompt="Primary Redis URL",
        default=context.current("REDIS_URL") or "redis://localhost:6379/0",
        required=True,
    )
    validate_redis_url(primary, require_tls=context.profile != "demo", role="Primary")
    context.set_backend("REDIS_URL", primary)
    redis_targets: dict[str, str] = {"Primary": primary}

    def _configure_optional(key: str, label: str) -> None:
        value = provider.prompt_string(
            key=key,
            prompt=f"{label} Redis URL (blank = reuse primary)",
            default=context.current(key) or "",
            required=False,
        )
        if value:
            validate_redis_url(value, require_tls=context.profile != "demo", role=label)
            context.set_backend(key, value)
            redis_targets[label] = value
        else:
            context.set_backend(key, "")
            if context.profile != "demo":
                context.console.warn(
                    f"{label} Redis workloads will reuse the primary Redis instance. "
                    "Provision a dedicated pool in production.",
                    topic="redis",
                )

    _configure_optional("RATE_LIMIT_REDIS_URL", "Rate limiting")
    _configure_optional("AUTH_CACHE_REDIS_URL", "Auth/session cache")
    _configure_optional("SECURITY_TOKEN_REDIS_URL", "Security token")

    billing = provider.prompt_string(
        key="BILLING_EVENTS_REDIS_URL",
        prompt="Billing events Redis URL (blank = reuse primary)",
        default=context.current("BILLING_EVENTS_REDIS_URL") or "",
        required=False,
    )
    if billing:
        validate_redis_url(billing, require_tls=context.profile != "demo", role="Billing events")
        context.set_backend("BILLING_EVENTS_REDIS_URL", billing)
        redis_targets["Billing events"] = billing
    else:
        context.set_backend("BILLING_EVENTS_REDIS_URL", "")
        if context.profile != "demo":
            context.console.warn(
                "Using the primary Redis instance for billing streams. Provision a dedicated "
                "instance for production.",
                topic="redis",
            )
    _warmup_redis(context, redis_targets)


def _collect_billing(context: WizardContext, provider: InputProvider) -> None:
    enable_billing = provider.prompt_bool(
        key="ENABLE_BILLING",
        prompt="Enable billing endpoints now?",
        default=context.current_bool("ENABLE_BILLING", False),
    )
    context.set_backend_bool("ENABLE_BILLING", enable_billing)
    context.set_frontend_bool("NEXT_PUBLIC_ENABLE_BILLING", enable_billing)

    enable_stream = provider.prompt_bool(
        key="ENABLE_BILLING_STREAM",
        prompt="Enable billing stream (Redis SSE)?",
        default=context.current_bool("ENABLE_BILLING_STREAM", False),
    )
    context.set_backend_bool("ENABLE_BILLING_STREAM", enable_stream)

    if not enable_billing:
        context.console.info("Stripe secrets skipped (ENABLE_BILLING=false).", topic="wizard")
        return

    secret = provider.prompt_secret(
        key="STRIPE_SECRET_KEY",
        prompt="Stripe secret key",
        existing=context.current("STRIPE_SECRET_KEY"),
        required=True,
    )
    webhook = _maybe_generate_webhook_secret(context, provider)
    if not webhook:
        webhook = provider.prompt_secret(
            key="STRIPE_WEBHOOK_SECRET",
            prompt="Stripe webhook signing secret",
            existing=context.current("STRIPE_WEBHOOK_SECRET"),
            required=True,
        )
    plan_map_raw = provider.prompt_string(
        key="STRIPE_PRODUCT_PRICE_MAP",
        prompt="Stripe product price map (JSON)",
        default=(
            context.current("STRIPE_PRODUCT_PRICE_MAP")
            or '{"starter":"price_xxx","pro":"price_xxx"}'
        ),
        required=True,
    )
    validated = validate_plan_map(plan_map_raw)
    context.set_backend("STRIPE_SECRET_KEY", secret, mask=True)
    context.set_backend("STRIPE_WEBHOOK_SECRET", webhook, mask=True)
    context.set_backend(
        "STRIPE_PRODUCT_PRICE_MAP",
        json.dumps(validated, separators=(",", ":")),
    )

    _maybe_run_stripe_setup(context, provider)


def _maybe_generate_webhook_secret(context: WizardContext, provider: InputProvider) -> str | None:
    allow_auto = context.profile == "demo" and not context.is_headless
    if not allow_auto:
        return None

    default_yes = not bool(context.current("STRIPE_WEBHOOK_SECRET"))
    if not provider.prompt_bool(
        key="STRIPE_WEBHOOK_SECRET_AUTO",
        prompt="Generate webhook signing secret via Stripe CLI now?",
        default=default_yes,
    ):
        return None

    forward_url = f"{context.api_base_url.rstrip('/')}/api/v1/webhooks/stripe"
    try:
        if context.cli_ctx.presenter is None:  # pragma: no cover - defensive
            raise CLIError("Presenter not initialized.")
        prompt = context.cli_ctx.presenter.prompt
        stripe_cli = StripeCli()
        ensure_stripe_cli(
            cli=stripe_cli,
            console=context.console,
            prompt=prompt,
            non_interactive=False,
        )
        secret = stripe_cli.capture_webhook_secret(forward_url)
    except CLIError as exc:
        context.console.warn(f"Stripe CLI webhook capture failed: {exc}", topic="stripe")
        return None

    context.console.success("Captured webhook signing secret via Stripe CLI.", topic="stripe")
    return secret


def _collect_email(context: WizardContext, provider: InputProvider) -> None:
    enable_resend = provider.prompt_bool(
        key="RESEND_EMAIL_ENABLED",
        prompt="Enable Resend email delivery?",
        default=context.current_bool("RESEND_EMAIL_ENABLED", False),
    )
    context.set_backend_bool("RESEND_EMAIL_ENABLED", enable_resend)
    base_url = provider.prompt_string(
        key="RESEND_BASE_URL",
        prompt="Resend API base URL",
        default=context.current("RESEND_BASE_URL") or "https://api.resend.com",
        required=True,
    )
    context.set_backend("RESEND_BASE_URL", base_url)
    if not enable_resend:
        return

    api_key = provider.prompt_secret(
        key="RESEND_API_KEY",
        prompt="Resend API key",
        existing=context.current("RESEND_API_KEY"),
        required=True,
    )
    default_from = provider.prompt_string(
        key="RESEND_DEFAULT_FROM",
        prompt="Default From address",
        default=context.current("RESEND_DEFAULT_FROM") or "support@example.com",
        required=True,
    )
    template_verify = provider.prompt_string(
        key="RESEND_EMAIL_VERIFICATION_TEMPLATE_ID",
        prompt="Verification template ID (optional)",
        default=context.current("RESEND_EMAIL_VERIFICATION_TEMPLATE_ID") or "",
        required=False,
    )
    template_reset = provider.prompt_string(
        key="RESEND_PASSWORD_RESET_TEMPLATE_ID",
        prompt="Password reset template ID (optional)",
        default=context.current("RESEND_PASSWORD_RESET_TEMPLATE_ID") or "",
        required=False,
    )
    context.set_backend("RESEND_API_KEY", api_key, mask=True)
    context.set_backend("RESEND_DEFAULT_FROM", default_from)
    context.set_backend("RESEND_EMAIL_VERIFICATION_TEMPLATE_ID", template_verify)
    context.set_backend("RESEND_PASSWORD_RESET_TEMPLATE_ID", template_reset)


def _collect_sso(context: WizardContext, provider: InputProvider) -> None:
    enabled_key = env_key(GOOGLE_PROVIDER_KEY, "ENABLED")
    enabled = provider.prompt_bool(
        key=enabled_key,
        prompt="Enable Google SSO (OIDC)?",
        default=context.current_bool(enabled_key, False),
    )
    context.set_backend_bool(enabled_key, enabled)
    if not enabled:
        context.console.info("Google SSO disabled.", topic="sso")
        return

    app_public_url = (context.current("APP_PUBLIC_URL") or "").strip().rstrip("/")
    if app_public_url:
        redirect_uri = f"{app_public_url}/auth/sso/{GOOGLE_PROVIDER_KEY}/callback"
        context.console.info(
            f"Register redirect URI: {redirect_uri}",
            topic="sso",
        )

    scope_key = env_key(GOOGLE_PROVIDER_KEY, "SCOPE")
    scope_mode = provider.prompt_choice(
        key=scope_key,
        prompt="SSO config scope",
        choices=SCOPE_MODE_CHOICES,
        default=context.current(scope_key) or DEFAULT_SCOPE_MODE,
    ).strip()
    context.set_backend(scope_key, scope_mode)

    tenant_slug_key = env_key(GOOGLE_PROVIDER_KEY, "TENANT_SLUG")
    tenant_id_key = env_key(GOOGLE_PROVIDER_KEY, "TENANT_ID")
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

    issuer_key = env_key(GOOGLE_PROVIDER_KEY, "ISSUER_URL")
    issuer_url = provider.prompt_string(
        key=issuer_key,
        prompt="OIDC issuer URL",
        default=context.current(issuer_key) or GOOGLE_ISSUER_URL,
        required=True,
    ).strip()
    if not issuer_url:
        raise CLIError("OIDC issuer URL is required.")
    context.set_backend(issuer_key, issuer_url)

    discovery_key = env_key(GOOGLE_PROVIDER_KEY, "DISCOVERY_URL")
    discovery_url = provider.prompt_string(
        key=discovery_key,
        prompt="OIDC discovery URL (blank = issuer/.well-known)",
        default=context.current(discovery_key) or GOOGLE_DISCOVERY_URL,
        required=False,
    ).strip()
    context.set_backend(discovery_key, discovery_url)

    client_id_key = env_key(GOOGLE_PROVIDER_KEY, "CLIENT_ID")
    client_id = provider.prompt_string(
        key=client_id_key,
        prompt="Google client ID",
        default=context.current(client_id_key) or "",
        required=True,
    ).strip()
    if not client_id:
        raise CLIError("Google client ID is required.")
    context.set_backend(client_id_key, client_id)

    token_auth_key = env_key(GOOGLE_PROVIDER_KEY, "TOKEN_AUTH_METHOD")
    id_token_algs_key = env_key(GOOGLE_PROVIDER_KEY, "ID_TOKEN_ALGS")
    has_existing_advanced = bool(
        (context.current(token_auth_key) or "").strip()
        or (context.current(id_token_algs_key) or "").strip()
    )
    use_advanced = provider.prompt_bool(
        key="SSO_GOOGLE_ADVANCED_SETTINGS",
        prompt="Configure advanced SSO settings (token auth method, ID token algs)?",
        default=has_existing_advanced,
    )
    if use_advanced:
        token_auth_raw = provider.prompt_choice(
            key=token_auth_key,
            prompt="Token endpoint auth method",
            choices=TOKEN_AUTH_METHOD_CHOICES,
            default=context.current(token_auth_key) or DEFAULT_TOKEN_AUTH_METHOD,
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
            context.current(token_auth_key) or DEFAULT_TOKEN_AUTH_METHOD
        )
        allowed_id_token_algs = parse_id_token_algs(context.current(id_token_algs_key) or "")

    context.set_backend(token_auth_key, token_auth_method)
    context.set_backend(id_token_algs_key, ",".join(allowed_id_token_algs))

    client_secret_key = env_key(GOOGLE_PROVIDER_KEY, "CLIENT_SECRET")
    client_secret_required = token_auth_method in {"client_secret_basic", "client_secret_post"}
    client_secret = provider.prompt_secret(
        key=client_secret_key,
        prompt="Google client secret",
        existing=context.current(client_secret_key),
        required=client_secret_required,
    )
    if client_secret_required and not client_secret:
        raise CLIError("Google client secret is required.")
    context.set_backend(client_secret_key, client_secret, mask=True)

    scopes_key = env_key(GOOGLE_PROVIDER_KEY, "SCOPES")
    scopes_raw = provider.prompt_string(
        key=scopes_key,
        prompt="OIDC scopes (comma-separated)",
        default=context.current(scopes_key) or ",".join(DEFAULT_SCOPES),
        required=True,
    )
    scopes = parse_scopes(scopes_raw)
    context.set_backend(scopes_key, ",".join(scopes))

    pkce_key = env_key(GOOGLE_PROVIDER_KEY, "PKCE_REQUIRED")
    pkce_required = provider.prompt_bool(
        key=pkce_key,
        prompt="Require PKCE (recommended)?",
        default=context.current_bool(pkce_key, True),
    )
    if token_auth_method == "none" and not pkce_required:
        raise CLIError("Token auth method 'none' requires PKCE.")
    context.set_backend_bool(pkce_key, pkce_required)

    policy_key = env_key(GOOGLE_PROVIDER_KEY, "AUTO_PROVISION_POLICY")
    policy_raw = provider.prompt_choice(
        key=policy_key,
        prompt="SSO auto-provision policy",
        choices=AUTO_PROVISION_POLICIES,
        default=context.current(policy_key) or DEFAULT_AUTO_PROVISION_POLICY,
    )
    policy = normalize_policy(policy_raw)
    context.set_backend(policy_key, policy)

    allowed_domains_key = env_key(GOOGLE_PROVIDER_KEY, "ALLOWED_DOMAINS")
    default_role_key = env_key(GOOGLE_PROVIDER_KEY, "DEFAULT_ROLE")
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
            default=context.current(default_role_key) or DEFAULT_ROLE,
        )
        role = normalize_role(role_raw)
        context.set_backend(default_role_key, role)
    else:
        context.set_backend(allowed_domains_key, "")
        context.set_backend(default_role_key, context.current(default_role_key) or DEFAULT_ROLE)

def _warmup_redis(context: WizardContext, targets: dict[str, str]) -> None:
    record = context.automation.get(AutomationPhase.REDIS)
    if not record.enabled:
        return
    if record.status == AutomationStatus.BLOCKED:
        context.console.warn(record.note or "Redis automation blocked.", topic="redis")
        context.refresh_automation_ui(AutomationPhase.REDIS)
        return
    context.automation.update(
        AutomationPhase.REDIS,
        AutomationStatus.RUNNING,
        "Validating Redis connectivity.",
    )
    context.refresh_automation_ui(AutomationPhase.REDIS)
    try:
        _ping_all_redis(targets)
    except Exception as exc:  # pragma: no cover - network failures
        context.automation.update(
            AutomationPhase.REDIS,
            AutomationStatus.FAILED,
            f"Redis warm-up failed: {exc}",
        )
        context.refresh_automation_ui(AutomationPhase.REDIS)
        raise CLIError(f"Redis warm-up failed: {exc}") from exc
    else:
        context.automation.update(
            AutomationPhase.REDIS,
            AutomationStatus.SUCCEEDED,
            "Redis warm-up succeeded.",
        )
        context.refresh_automation_ui(AutomationPhase.REDIS)
        context.console.success("Redis pools validated.", topic="redis")


def _ping_all_redis(targets: dict[str, str]) -> None:
    seen: set[str] = set()
    for _, url in targets.items():
        if not url or url in seen:
            continue
        seen.add(url)
        client = Redis.from_url(url, encoding="utf-8", decode_responses=True)
        try:
            client.ping()
        finally:
            client.close()


def _maybe_run_migrations(context: WizardContext, provider: InputProvider) -> None:
    record = context.automation.get(AutomationPhase.MIGRATIONS)
    if record.enabled:
        if record.status == AutomationStatus.BLOCKED:
            context.console.warn(record.note or "Migrations automation blocked.", topic="migrate")
            context.refresh_automation_ui(AutomationPhase.MIGRATIONS)
            return
        context.automation.update(
            AutomationPhase.MIGRATIONS,
            AutomationStatus.RUNNING,
            "Running `just migrate`.",
        )
        context.refresh_automation_ui(AutomationPhase.MIGRATIONS)
        try:
            context.run_migrations()
        except (CLIError, subprocess.CalledProcessError) as exc:
            context.automation.update(
                AutomationPhase.MIGRATIONS,
                AutomationStatus.FAILED,
                f"Migrations failed: {exc}",
            )
            context.refresh_automation_ui(AutomationPhase.MIGRATIONS)
            raise
        else:
            context.automation.update(
                AutomationPhase.MIGRATIONS,
                AutomationStatus.SUCCEEDED,
                "Database migrated.",
            )
            context.refresh_automation_ui(AutomationPhase.MIGRATIONS)
        return

    run_now = provider.prompt_bool(
        key="RUN_MIGRATIONS_NOW",
        prompt="Run `just migrate` now?",
        default=context.profile != "demo",
    )
    if run_now:
        context.run_migrations()
def _maybe_run_stripe_setup(context: WizardContext, provider: InputProvider) -> None:
    record = context.automation.get(AutomationPhase.STRIPE)
    if record.enabled:
        if record.status == AutomationStatus.BLOCKED:
            context.console.warn(
                f"Stripe automation blocked: {record.note or 'unmet prerequisites.'}",
                topic="stripe",
            )
            return
        if context.is_headless:
            context.console.warn(
                "Stripe automation skipped in headless mode; run the setup command manually.",
                topic="stripe",
            )
            context.automation.update(
                AutomationPhase.STRIPE,
                AutomationStatus.SKIPPED,
                "Headless mode skips Stripe automation.",
            )
            context.refresh_automation_ui(AutomationPhase.STRIPE)
            return
        context.automation.update(
            AutomationPhase.STRIPE,
            AutomationStatus.RUNNING,
            "Running `stripe setup` helper.",
        )
        context.refresh_automation_ui(AutomationPhase.STRIPE)
        context.console.info("Running embedded Stripe setup flow …", topic="stripe")
        try:
            context.run_subprocess(
                ["python", "-m", "starter_console.app", "stripe", "setup"],
                topic="stripe",
            )
        except (CLIError, subprocess.CalledProcessError) as exc:
            context.automation.update(
                AutomationPhase.STRIPE,
                AutomationStatus.FAILED,
                f"Stripe setup failed: {exc}",
            )
            context.refresh_automation_ui(AutomationPhase.STRIPE)
            raise
        else:
            context.automation.update(
                AutomationPhase.STRIPE,
                AutomationStatus.SUCCEEDED,
                "Stripe setup completed.",
            )
            context.refresh_automation_ui(AutomationPhase.STRIPE)
            context.record_verification(
                provider="stripe",
                identifier="stripe_setup",
                status="passed",
                detail="Plans seeded via CLI.",
                source="wizard",
            )
        return

    if context.is_headless:
        context.console.warn(
            "Headless run detected. Run `starter-console stripe setup` manually to seed "
            "plans.",
            topic="stripe",
        )
        return

    should_seed = provider.prompt_bool(
        key="RUN_STRIPE_SEED",
        prompt="Run the Stripe setup helper now?",
        default=False,
    )
    if should_seed:
        try:
            context.run_subprocess(
                ["python", "-m", "starter_console.app", "stripe", "setup"],
                topic="stripe",
            )
        except (CLIError, subprocess.CalledProcessError) as exc:
            context.record_verification(
                provider="stripe",
                identifier="stripe_setup",
                status="failed",
                detail=str(exc),
                source="wizard",
            )
            raise
        else:
            context.record_verification(
                provider="stripe",
                identifier="stripe_setup",
                status="passed",
                detail="Plans seeded via CLI.",
                source="wizard",
            )
