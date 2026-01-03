from __future__ import annotations

import json

from starter_contracts.secrets.models import SecretsProviderLiteral

from starter_console.core import CLIError

from ...inputs import InputProvider, is_headless_provider
from ..context import WizardContext
from ..presets import apply_hosting_preset
from ._prompts import prompt_nonempty_string

_DEFAULT_AUTH_AUDIENCE = (
    "agent-api,analytics-service,billing-worker,support-console,synthetic-monitor"
)
_KEY_STORAGE_CHOICES = {"file", "secret-manager"}
_KEY_STORAGE_PROVIDER_CHOICES = {literal.value for literal in SecretsProviderLiteral}
_HOSTING_PRESET_CHOICES = ["local_docker", "cloud_managed", "enterprise_custom"]
_CLOUD_PROVIDER_CHOICES = ["aws", "azure", "gcp", "other"]


def run(context: WizardContext, provider: InputProvider) -> None:
    """Collect deployment metadata shared across all milestones."""

    context.console.section(
        "Profile & Core",
        "Choose hosting defaults, then establish baseline URLs and auth defaults.",
    )

    _configure_setup_preferences(context, provider)
    apply_hosting_preset(context)

    env_default = {
        "demo": "development",
        "staging": "staging",
        "production": "production",
    }[context.profile]
    environment = provider.prompt_string(
        key="ENVIRONMENT",
        prompt="Environment label (ENVIRONMENT)",
        default=context.current("ENVIRONMENT") or env_default,
        required=True,
    )
    context.set_backend("ENVIRONMENT", environment)

    debug_default = context.current_bool("DEBUG", default=context.profile == "demo")
    debug = provider.prompt_bool(
        key="DEBUG",
        prompt="Enable FastAPI debug mode?",
        default=debug_default,
    )
    context.set_backend_bool("DEBUG", debug)

    port = provider.prompt_string(
        key="PORT",
        prompt="FastAPI port (PORT)",
        default=context.current("PORT") or "8000",
        required=True,
    )
    context.set_backend("PORT", port)

    app_public_url = provider.prompt_string(
        key="APP_PUBLIC_URL",
        prompt="Public site base URL (APP_PUBLIC_URL)",
        default=context.current("APP_PUBLIC_URL") or "http://localhost:3000",
        required=True,
    )
    context.set_backend("APP_PUBLIC_URL", app_public_url)

    allowed_hosts = provider.prompt_string(
        key="ALLOWED_HOSTS",
        prompt="Allowed hosts (comma-separated)",
        default=context.current("ALLOWED_HOSTS")
        or "localhost,localhost:8000,127.0.0.1,testserver,testclient",
        required=True,
    )
    context.set_backend("ALLOWED_HOSTS", allowed_hosts)

    allowed_origins = provider.prompt_string(
        key="ALLOWED_ORIGINS",
        prompt="Allowed origins (comma-separated)",
        default=context.current("ALLOWED_ORIGINS")
        or "http://localhost:3000,http://localhost:8000",
        required=True,
    )
    context.set_backend("ALLOWED_ORIGINS", allowed_origins)

    allowed_methods = prompt_nonempty_string(
        context,
        provider,
        key="ALLOWED_METHODS",
        prompt="Allowed HTTP methods (comma-separated)",
        default=context.current("ALLOWED_METHODS") or "GET,POST,PUT,DELETE,OPTIONS",
    )
    context.set_backend("ALLOWED_METHODS", allowed_methods)

    allowed_headers = prompt_nonempty_string(
        context,
        provider,
        key="ALLOWED_HEADERS",
        prompt="Allowed headers (comma-separated)",
        default=context.current("ALLOWED_HEADERS") or "*",
    )
    context.set_backend("ALLOWED_HEADERS", allowed_headers)

    auto_run = provider.prompt_bool(
        key="AUTO_RUN_MIGRATIONS",
        prompt="Automatically run migrations on startup?",
        default=context.current_bool("AUTO_RUN_MIGRATIONS", default=context.profile == "demo"),
    )
    context.set_backend_bool("AUTO_RUN_MIGRATIONS", auto_run)

    port_int = int(port) if port.isdigit() else 8000
    api_base_url = provider.prompt_string(
        key="API_BASE_URL",
        prompt="API base URL for frontend + tooling",
        default=context.current("API_BASE_URL") or f"http://127.0.0.1:{port_int}",
        required=True,
    )
    context.api_base_url = api_base_url
    context.set_backend("API_BASE_URL", api_base_url)

    _configure_branding(context, provider)
    _configure_authentication(context, provider)
    _configure_database(context, provider)
    _configure_logging(context, provider)


def _configure_setup_preferences(context: WizardContext, provider: InputProvider) -> None:
    preset_default = _state_default(context, "SETUP_HOSTING_PRESET") or (
        "local_docker" if context.profile == "demo" else "cloud_managed"
    )
    hosting_preset = provider.prompt_choice(
        key="SETUP_HOSTING_PRESET",
        prompt="Hosting preset",
        choices=_HOSTING_PRESET_CHOICES,
        default=preset_default,
    )
    context.hosting_preset = hosting_preset

    cloud_provider = None
    if hosting_preset == "cloud_managed":
        cloud_default = _state_default(context, "SETUP_CLOUD_PROVIDER") or "aws"
        cloud_provider = provider.prompt_choice(
            key="SETUP_CLOUD_PROVIDER",
            prompt="Cloud provider (if using cloud managed hosting)",
            choices=_CLOUD_PROVIDER_CHOICES,
            default=cloud_default,
        )
    context.cloud_provider = cloud_provider

    advanced_default = _state_bool_default(
        context,
        "SETUP_SHOW_ADVANCED",
        default=context.profile in {"staging", "production"},
    )
    show_advanced = provider.prompt_bool(
        key="SETUP_SHOW_ADVANCED",
        prompt="Show advanced tuning prompts?",
        default=advanced_default,
    )
    context.show_advanced_prompts = show_advanced
    if show_advanced:
        context.console.info("Advanced prompts enabled.", topic="wizard")
    else:
        context.console.info("Advanced prompts hidden (defaults will apply).", topic="wizard")


def _configure_branding(context: WizardContext, provider: InputProvider) -> None:
    app_name = prompt_nonempty_string(
        context,
        provider,
        key="APP_NAME",
        prompt="Application name",
        default=context.current("APP_NAME") or "api-service",
    )
    context.set_backend("APP_NAME", app_name)

    app_description = prompt_nonempty_string(
        context,
        provider,
        key="APP_DESCRIPTION",
        prompt="Application description",
        default=context.current("APP_DESCRIPTION") or "api-service FastAPI microservice",
    )
    context.set_backend("APP_DESCRIPTION", app_description)

    app_version = prompt_nonempty_string(
        context,
        provider,
        key="APP_VERSION",
        prompt="Application version",
        default=context.current("APP_VERSION") or "1.0.0",
    )
    context.set_backend("APP_VERSION", app_version)


def _configure_authentication(context: WizardContext, provider: InputProvider) -> None:
    require_email = provider.prompt_bool(
        key="REQUIRE_EMAIL_VERIFICATION",
        prompt="Require verified email before accessing protected APIs?",
        default=context.current_bool("REQUIRE_EMAIL_VERIFICATION", True),
    )
    context.set_backend_bool("REQUIRE_EMAIL_VERIFICATION", require_email)

    audience_default = context.current("AUTH_AUDIENCE") or _DEFAULT_AUTH_AUDIENCE
    raw_audience = prompt_nonempty_string(
        context,
        provider,
        key="AUTH_AUDIENCE",
        prompt="JWT audiences (comma-separated or JSON array)",
        default=audience_default,
    )
    context.set_backend("AUTH_AUDIENCE", _normalize_audience_value(raw_audience))

    jwt_algorithm = prompt_nonempty_string(
        context,
        provider,
        key="JWT_ALGORITHM",
        prompt="JWT algorithm",
        default=context.current("JWT_ALGORITHM") or "HS256",
    )
    context.set_backend("JWT_ALGORITHM", jwt_algorithm)

    if context.profile in {"staging", "production"}:
        backend_choice = "secret-manager"
        context.console.info(
            "Key storage backend is forced to secret-manager for staging/production.",
            topic="wizard",
        )
    else:
        backend_choice = _prompt_choice(
            context,
            provider,
            key="AUTH_KEY_STORAGE_BACKEND",
            prompt="Key storage backend (file or secret-manager)",
            default=context.current("AUTH_KEY_STORAGE_BACKEND") or "file",
            choices=_KEY_STORAGE_CHOICES,
        )
    context.set_backend("AUTH_KEY_STORAGE_BACKEND", backend_choice)

    if backend_choice == "file":
        storage_path = prompt_nonempty_string(
            context,
            provider,
            key="AUTH_KEY_STORAGE_PATH",
            prompt="Key storage path",
            default=context.current("AUTH_KEY_STORAGE_PATH") or "var/keys/keyset.json",
        )
        context.set_backend("AUTH_KEY_STORAGE_PATH", storage_path)
        context.unset_backend("AUTH_KEY_STORAGE_PROVIDER")
    else:
        context.unset_backend("AUTH_KEY_STORAGE_PATH")
        provider_default = (
            context.current("AUTH_KEY_STORAGE_PROVIDER")
            or context.current("SECRETS_PROVIDER")
            or (
                SecretsProviderLiteral.VAULT_DEV.value
                if context.profile == "demo"
                else SecretsProviderLiteral.AWS_SM.value
            )
        )
        provider_choice = _prompt_choice(
            context,
            provider,
            key="AUTH_KEY_STORAGE_PROVIDER",
            prompt="Key storage provider (vault/infisical/aws/azure/gcp)",
            default=provider_default,
            choices=_KEY_STORAGE_PROVIDER_CHOICES,
        )
        context.set_backend("AUTH_KEY_STORAGE_PROVIDER", provider_choice)

    secret_required = backend_choice != "file"
    secret_default = context.current("AUTH_KEY_SECRET_NAME") or ""
    while True:
        secret_name = provider.prompt_string(
            key="AUTH_KEY_SECRET_NAME",
            prompt="Secret-manager key name (when using secret-manager)",
            default=secret_default,
            required=secret_required,
        ).strip()
        if secret_required and not secret_name:
            if _is_headless(provider):
                raise CLIError("AUTH_KEY_SECRET_NAME is required when using secret-manager.")
            context.console.warn(
                "AUTH_KEY_SECRET_NAME is required when using secret-manager.",
                topic="wizard",
            )
            continue
        break
    if secret_name:
        context.set_backend("AUTH_KEY_SECRET_NAME", secret_name)
    elif not secret_required:
        context.unset_backend("AUTH_KEY_SECRET_NAME")


def _configure_database(context: WizardContext, provider: InputProvider) -> None:
    database_echo = provider.prompt_bool(
        key="DATABASE_ECHO",
        prompt="Enable SQLAlchemy echo logging?",
        default=context.current_bool("DATABASE_ECHO", False),
    )
    context.set_backend_bool("DATABASE_ECHO", database_echo)

    _prompt_positive_int(
        context,
        provider,
        key="DATABASE_POOL_SIZE",
        prompt="Database pool size",
        default=context.current("DATABASE_POOL_SIZE") or "5",
    )
    _prompt_positive_int(
        context,
        provider,
        key="DATABASE_MAX_OVERFLOW",
        prompt="Database pool max overflow",
        default=context.current("DATABASE_MAX_OVERFLOW") or "10",
    )
    _prompt_positive_int(
        context,
        provider,
        key="DATABASE_POOL_RECYCLE",
        prompt="Database pool recycle seconds",
        default=context.current("DATABASE_POOL_RECYCLE") or "1800",
    )
    _prompt_positive_float(
        context,
        provider,
        key="DATABASE_POOL_TIMEOUT",
        prompt="Database pool timeout (seconds)",
        default=context.current("DATABASE_POOL_TIMEOUT") or "30.0",
    )
    _prompt_positive_float(
        context,
        provider,
        key="DATABASE_HEALTH_TIMEOUT",
        prompt="Database health check timeout (seconds)",
        default=context.current("DATABASE_HEALTH_TIMEOUT") or "5.0",
    )


def _configure_logging(context: WizardContext, provider: InputProvider) -> None:
    log_level = prompt_nonempty_string(
        context,
        provider,
        key="LOG_LEVEL",
        prompt="Logging level",
        default=context.current("LOG_LEVEL") or "INFO",
    )
    context.set_backend("LOG_LEVEL", log_level)


def _normalize_audience_value(raw_value: str) -> str:
    stripped = raw_value.strip()
    candidates: list[str] = []
    if not stripped:
        raise CLIError("AUTH_AUDIENCE must include at least one audience identifier.")
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list):
        candidates = [str(item).strip() for item in parsed if str(item).strip()]
    if not candidates:
        candidates = [part.strip() for part in stripped.split(",") if part.strip()]
    if not candidates:
        raise CLIError("AUTH_AUDIENCE must include at least one audience identifier.")
    deduped = list(dict.fromkeys(candidates))
    return json.dumps(deduped)


def _prompt_choice(
    context: WizardContext,
    provider: InputProvider,
    *,
    key: str,
    prompt: str,
    default: str,
    choices: set[str],
) -> str:
    choices_lower = {choice.lower() for choice in choices}
    while True:
        value = provider.prompt_string(
            key=key,
            prompt=f"{prompt} ({'/'.join(sorted(choices_lower))})",
            default=default,
            required=True,
        ).strip().lower()
        if value in choices_lower:
            return value
        if _is_headless(provider):
            raise CLIError(f"{key} must be one of {sorted(choices_lower)}.")
        context.console.warn(f"{key} must be one of {sorted(choices_lower)}.", topic="wizard")


def _prompt_positive_int(
    context: WizardContext,
    provider: InputProvider,
    *,
    key: str,
    prompt: str,
    default: str,
) -> int:
    while True:
        raw = provider.prompt_string(
            key=key,
            prompt=prompt,
            default=default,
            required=True,
        ).strip()
        try:
            value = int(raw)
        except ValueError:
            if _is_headless(provider):
                raise CLIError(f"{key} must be an integer.") from None
            context.console.warn(f"{key} must be an integer.", topic="wizard")
            continue
        if value <= 0:
            if _is_headless(provider):
                raise CLIError(f"{key} must be greater than zero.")
            context.console.warn(f"{key} must be greater than zero.", topic="wizard")
            continue
        context.set_backend(key, str(value))
        return value


def _prompt_positive_float(
    context: WizardContext,
    provider: InputProvider,
    *,
    key: str,
    prompt: str,
    default: str,
) -> float:
    while True:
        raw = provider.prompt_string(
            key=key,
            prompt=prompt,
            default=default,
            required=True,
        ).strip()
        try:
            value = float(raw)
        except ValueError:
            if _is_headless(provider):
                raise CLIError(f"{key} must be a number.") from None
            context.console.warn(f"{key} must be a number.", topic="wizard")
            continue
        if value <= 0:
            if _is_headless(provider):
                raise CLIError(f"{key} must be greater than zero.")
            context.console.warn(f"{key} must be greater than zero.", topic="wizard")
            continue
        context.set_backend(key, str(value))
        return value


def _is_headless(provider: InputProvider) -> bool:
    return is_headless_provider(provider)


def _state_default(context: WizardContext, key: str) -> str | None:
    if context.state_store is None:
        return None
    return context.state_store.snapshot().get(key)


def _state_bool_default(context: WizardContext, key: str, *, default: bool) -> bool:
    raw = _state_default(context, key)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    return default
