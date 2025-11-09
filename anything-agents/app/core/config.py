# File: app/core/config.py
# Purpose: Configuration management for anything-agents
# Dependencies: pydantic-settings, python-dotenv
# Used by: main.py and other modules requiring configuration

import json
from functools import lru_cache

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings

DEFAULT_SECRET_KEY = "your-secret-key-here-change-in-production"
DEFAULT_PASSWORD_PEPPER = "local-dev-password-pepper"
DEFAULT_REFRESH_TOKEN_PEPPER = "local-dev-refresh-pepper"
DEFAULT_KEY_STORAGE_PATH = "var/keys/keyset.json"
PLACEHOLDER_SECRET_KEY = "change-me"
PLACEHOLDER_PASSWORD_PEPPER = "change-me-too"
PLACEHOLDER_REFRESH_TOKEN_PEPPER = "change-me-again"
_SAFE_ENVIRONMENTS = {"development", "dev", "local", "test"}

# =============================================================================
# SETTINGS CLASS
# =============================================================================


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses Pydantic Settings for type validation and environment loading.
    """

    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================

    app_name: str = Field(default="anything-agents", description="Application name")
    app_description: str = Field(
        default="anything-agents FastAPI microservice", description="Application description"
    )
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(
        default="development",
        description="Deployment environment label (development, staging, production, etc.)",
        alias="ENVIRONMENT",
    )
    port: int = Field(default=8000, description="Server port")

    # =============================================================================
    # AI API KEYS
    # =============================================================================

    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    gemini_api_key: str | None = Field(default=None, description="Google Gemini API key")
    xai_api_key: str | None = Field(default=None, description="xAI API key")

    # =============================================================================
    # AI TOOLS API KEYS
    # =============================================================================

    tavily_api_key: str | None = Field(default=None, description="Tavily web search API key")

    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================

    secret_key: str = Field(default=DEFAULT_SECRET_KEY, description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration time in minutes"
    )

    # =============================================================================
    # REDIS SETTINGS
    # =============================================================================

    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # =============================================================================
    # RATE LIMITING SETTINGS
    # =============================================================================

    chat_rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum chat completions allowed per user per minute.",
        alias="CHAT_RATE_LIMIT_PER_MINUTE",
    )
    chat_stream_rate_limit_per_minute: int = Field(
        default=30,
        description="Maximum streaming chat sessions started per user per minute.",
        alias="CHAT_STREAM_RATE_LIMIT_PER_MINUTE",
    )
    chat_stream_concurrent_limit: int = Field(
        default=5,
        description="Simultaneous streaming chat sessions allowed per user.",
        alias="CHAT_STREAM_CONCURRENT_LIMIT",
    )
    billing_stream_rate_limit_per_minute: int = Field(
        default=20,
        description="Maximum billing stream subscriptions allowed per tenant per minute.",
        alias="BILLING_STREAM_RATE_LIMIT_PER_MINUTE",
    )
    billing_stream_concurrent_limit: int = Field(
        default=3,
        description="Simultaneous billing stream connections allowed per tenant.",
        alias="BILLING_STREAM_CONCURRENT_LIMIT",
    )
    rate_limit_key_prefix: str = Field(
        default="rate-limit",
        description="Redis key namespace used by the rate limiter service.",
        alias="RATE_LIMIT_KEY_PREFIX",
    )

    # =============================================================================
    # SIGNUP / TENANT ONBOARDING
    # =============================================================================

    allow_public_signup: bool = Field(
        default=True,
        description="Allow unauthenticated tenants to self-register via /auth/register.",
    )
    allow_signup_trial_override: bool = Field(
        default=False,
        description=(
            "Permit /auth/register callers to request trial periods up to the plan/default cap."
        ),
    )
    signup_rate_limit_per_hour: int = Field(
        default=20,
        description="Maximum signup attempts permitted per IP address each hour.",
    )
    signup_default_plan_code: str | None = Field(
        default="starter",
        description="Plan code automatically provisioned for new tenants when billing is enabled.",
    )
    signup_default_trial_days: int = Field(
        default=14,
        description=(
            "Fallback trial length (days) for tenants when processor metadata is unavailable."
        ),
    )

    # =============================================================================
    # CORS SETTINGS (simplified to avoid parsing issues)
    # =============================================================================

    allowed_origins: str = Field(
        default="http://localhost:8000,http://localhost:8080",
        description="CORS allowed origins (comma-separated)",
    )
    allowed_methods: str = Field(
        default="GET,POST,PUT,DELETE,OPTIONS", description="CORS allowed methods (comma-separated)"
    )
    allowed_headers: str = Field(default="*", description="CORS allowed headers (comma-separated)")

    # =============================================================================
    # AUTHENTICATION SETTINGS
    # =============================================================================

    auth_audience: list[str] = Field(
        default_factory=lambda: [
            "agent-api",
            "analytics-service",
            "billing-worker",
            "support-console",
            "synthetic-monitor",
        ],
        description=(
            "Ordered list of permitted JWT audiences. "
            "Provide as JSON array via AUTH_AUDIENCE environment variable; "
            "comma-separated strings are accepted when instantiating Settings directly."
        ),
    )
    auth_key_storage_backend: str = Field(
        default="file",
        description="Key storage backend (file or secret-manager).",
    )
    auth_key_storage_path: str = Field(
        default=DEFAULT_KEY_STORAGE_PATH,
        description="Filesystem path for keyset JSON when using file backend.",
    )
    auth_key_secret_name: str | None = Field(
        default=None,
        description="Secret-manager key/path storing keyset JSON when backend=secret-manager.",
    )
    auth_jwks_cache_seconds: int = Field(
        default=300,
        description="Cache max-age for /.well-known/jwks.json responses.",
        alias="AUTH_JWKS_CACHE_SECONDS",
    )
    auth_jwks_max_age_seconds: int = Field(
        default=300,
        description="Preferred Cache-Control max-age for JWKS responses.",
        alias="AUTH_JWKS_MAX_AGE_SECONDS",
    )
    auth_jwks_etag_salt: str = Field(
        default="local-jwks-salt",
        description="Salt mixed into JWKS ETag derivation to avoid predictable hashes.",
        alias="AUTH_JWKS_ETAG_SALT",
    )
    auth_refresh_token_pepper: str = Field(
        default=DEFAULT_REFRESH_TOKEN_PEPPER,
        description="Server-side pepper prepended when hashing refresh tokens.",
        alias="AUTH_REFRESH_TOKEN_PEPPER",
    )
    auth_password_pepper: str = Field(
        default=DEFAULT_PASSWORD_PEPPER,
        description="Pepper prepended to human passwords prior to hashing.",
        alias="AUTH_PASSWORD_PEPPER",
    )
    auth_refresh_token_ttl_minutes: int = Field(
        default=43200,
        description="Default refresh token lifetime for human users (minutes).",
        alias="AUTH_REFRESH_TOKEN_TTL_MINUTES",
    )
    auth_password_history_count: int = Field(
        default=5,
        description="Number of historical password hashes retained per user.",
        alias="AUTH_PASSWORD_HISTORY_COUNT",
    )
    auth_lockout_threshold: int = Field(
        default=5,
        description="Failed login attempts allowed before locking the account.",
        alias="AUTH_LOCKOUT_THRESHOLD",
    )
    auth_lockout_window_minutes: float = Field(
        default=60.0,
        description="Rolling window in minutes for lockout threshold calculations.",
        alias="AUTH_LOCKOUT_WINDOW_MINUTES",
    )
    auth_lockout_duration_minutes: float = Field(
        default=60.0,
        description="Automatic unlock window for locked users (minutes).",
        alias="AUTH_LOCKOUT_DURATION_MINUTES",
    )
    auth_ip_lockout_threshold: int = Field(
        default=50,
        description="Failed attempts per IP or /24 subnet per minute before throttling.",
        alias="AUTH_IP_LOCKOUT_THRESHOLD",
    )
    auth_ip_lockout_window_minutes: int = Field(
        default=10,
        description="Window in minutes used for IP-based throttling heuristics.",
        alias="AUTH_IP_LOCKOUT_WINDOW_MINUTES",
    )
    auth_ip_lockout_duration_minutes: int = Field(
        default=10,
        description="Duration in minutes to block an IP/subnet after threshold breaches.",
        alias="AUTH_IP_LOCKOUT_DURATION_MINUTES",
    )

    # =============================================================================
    # LOGGING SETTINGS
    # =============================================================================

    log_level: str = Field(default="INFO", description="Logging level")

    # =============================================================================
    # VAULT SETTINGS
    # =============================================================================

    vault_addr: str | None = Field(
        default=None,
        description="HashiCorp Vault address for Transit verification.",
        alias="VAULT_ADDR",
    )
    vault_token: str | None = Field(
        default=None,
        description="Vault token/AppRole secret with transit:verify capability.",
        alias="VAULT_TOKEN",
    )
    vault_transit_key: str = Field(
        default="auth-service",
        description="Transit key name used for signing/verification.",
        alias="VAULT_TRANSIT_KEY",
    )
    vault_verify_enabled: bool = Field(
        default=False,
        description="When true, enforce Vault Transit verification for service-account issuance.",
        alias="VAULT_VERIFY_ENABLED",
    )

    # =============================================================================
    # DATABASE SETTINGS
    # =============================================================================

    database_url: str | None = Field(
        default=None,
        description="Async SQLAlchemy URL for the primary Postgres database",
        alias="DATABASE_URL",
    )
    database_pool_size: int = Field(
        default=5,
        description="SQLAlchemy async pool size",
    )
    database_max_overflow: int = Field(
        default=10,
        description="Maximum overflow connections for the SQLAlchemy pool",
    )
    database_pool_recycle: int = Field(
        default=1800,
        description="Seconds before recycling idle connections",
    )
    database_pool_timeout: float = Field(
        default=30.0,
        description="Seconds to wait for a connection from the pool",
    )
    database_health_timeout: float = Field(
        default=5.0,
        description="Timeout for database health checks (seconds)",
    )
    database_echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy engine echo for debugging",
    )
    enable_billing: bool = Field(
        default=False,
        description="Expose billing features and APIs once subscriptions are implemented",
    )
    enable_billing_stream: bool = Field(
        default=False,
        description="Enable real-time billing event streaming endpoints",
        alias="ENABLE_BILLING_STREAM",
    )
    enable_billing_retry_worker: bool = Field(
        default=True,
        description="Run the Stripe dispatch retry worker inside this process",
        alias="ENABLE_BILLING_RETRY_WORKER",
    )
    enable_billing_stream_replay: bool = Field(
        default=True,
        description="Replay processed Stripe events into Redis billing streams during startup",
        alias="ENABLE_BILLING_STREAM_REPLAY",
    )
    auto_run_migrations: bool = Field(
        default=False,
        description="Automatically run Alembic migrations on startup (dev convenience)",
    )

    billing_events_redis_url: str | None = Field(
        default=None,
        description="Redis URL used for billing event pub/sub (defaults to REDIS_URL when unset)",
        alias="BILLING_EVENTS_REDIS_URL",
    )

    # =============================================================================
    # BILLING / STRIPE SETTINGS
    # =============================================================================

    stripe_secret_key: str | None = Field(
        default=None,
        description="Stripe secret API key (sk_live_*/sk_test_*).",
        alias="STRIPE_SECRET_KEY",
    )
    stripe_webhook_secret: str | None = Field(
        default=None,
        description="Stripe webhook signing secret (whsec_*).",
        alias="STRIPE_WEBHOOK_SECRET",
    )
    stripe_product_price_map: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Mapping of billing plan codes to Stripe price IDs. Provide as JSON or "
            "comma-delimited entries such as 'starter=price_123,pro=price_456'."
        ),
        alias="STRIPE_PRODUCT_PRICE_MAP",
    )

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    @property
    def jwks_max_age_seconds(self) -> int:
        """Return preferred JWKS max-age in seconds."""

        return self.auth_jwks_max_age_seconds or self.auth_jwks_cache_seconds

    def get_allowed_origins_list(self) -> list[str]:
        """Get allowed origins as a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    def get_allowed_methods_list(self) -> list[str]:
        """Get allowed methods as a list."""
        return [method.strip() for method in self.allowed_methods.split(",") if method.strip()]

    def get_allowed_headers_list(self) -> list[str]:
        """Get allowed headers as a list."""
        return [header.strip() for header in self.allowed_headers.split(",") if header.strip()]

    def required_stripe_envs_missing(self) -> list[str]:
        """Return the list of Stripe environment variables missing when billing is enabled."""
        missing: list[str] = []
        if not (self.stripe_secret_key and self.stripe_secret_key.strip()):
            missing.append("STRIPE_SECRET_KEY")
        if not (self.stripe_webhook_secret and self.stripe_webhook_secret.strip()):
            missing.append("STRIPE_WEBHOOK_SECRET")
        if not self.stripe_product_price_map:
            missing.append("STRIPE_PRODUCT_PRICE_MAP")
        return missing

    def stripe_configuration_summary(self) -> dict[str, object]:
        """Return a masked summary of the active Stripe configuration for logging."""
        price_map = self.stripe_product_price_map or {}
        plan_codes = sorted(price_map.keys())
        redis_source = (
            "BILLING_EVENTS_REDIS_URL"
            if self.billing_events_redis_url
            else ("REDIS_URL" if self.redis_url else "<unset>")
        )
        return {
            "stripe_secret_key": self._mask_secret(self.stripe_secret_key),
            "stripe_webhook_secret": self._mask_secret(self.stripe_webhook_secret),
            "plans_configured": plan_codes,
            "plan_count": len(plan_codes),
            "billing_stream_enabled": self.enable_billing_stream,
            "billing_stream_backend": redis_source if self.enable_billing_stream else "disabled",
        }

    @staticmethod
    def _mask_secret(value: str | None) -> str:
        """Mask sensitive tokens while preserving enough characters for debugging."""
        if value is None:
            return "<missing>"
        cleaned = value.strip()
        if not cleaned:
            return "<missing>"
        if len(cleaned) <= 4:
            return "*" * len(cleaned)
        prefix = cleaned[:2]
        suffix = cleaned[-4:]
        middle_length = max(len(cleaned) - len(prefix) - len(suffix), 3)
        return f"{prefix}{'*' * middle_length}{suffix}"

    # =============================================================================
    # SECRET VALIDATION HELPERS
    # =============================================================================

    def secret_warnings(self) -> list[str]:
        warnings: list[str] = []
        if self._is_placeholder_secret(
            self.secret_key,
            {DEFAULT_SECRET_KEY, PLACEHOLDER_SECRET_KEY},
        ):
            warnings.append("SECRET_KEY is using the starter value")
        if self._is_placeholder_secret(
            self.auth_password_pepper,
            {DEFAULT_PASSWORD_PEPPER, PLACEHOLDER_PASSWORD_PEPPER},
        ):
            warnings.append("AUTH_PASSWORD_PEPPER is using the starter value")
        if self._is_placeholder_secret(
            self.auth_refresh_token_pepper,
            {DEFAULT_REFRESH_TOKEN_PEPPER, PLACEHOLDER_REFRESH_TOKEN_PEPPER},
        ):
            warnings.append("AUTH_REFRESH_TOKEN_PEPPER is using the starter value")
        if (
            self.auth_key_storage_backend == "file"
            and self.auth_key_storage_path == DEFAULT_KEY_STORAGE_PATH
        ):
            warnings.append("AUTH_KEY_STORAGE_PATH still points to var/keys/keyset.json")
        return warnings

    @staticmethod
    def _is_placeholder_secret(value: str | None, placeholders: set[str]) -> bool:
        if value is None:
            return True
        normalized = value.strip()
        if not normalized:
            return True
        return normalized in placeholders

    def should_enforce_secret_overrides(self) -> bool:
        env = (self.environment or "").lower()
        return not self.debug and env not in _SAFE_ENVIRONMENTS

    # =============================================================================
    # CONFIGURATION
    # =============================================================================

    model_config = {
        "env_file": (".env.local", ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @field_validator("auth_audience", mode="before")
    @classmethod
    def _parse_auth_audience(cls, value: str | list[str] | None) -> list[str] | None:
        """
        Normalize auth audience configuration to a list of non-empty strings.

        Supports comma-separated strings for environment-variable overrides.
        """
        if value is None:
            return None

        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
        elif isinstance(value, list | tuple | set):
            items = [str(item).strip() for item in value if str(item).strip()]
        else:
            raise ValueError("auth_audience must be a list or comma-separated string.")

        if not items:
            raise ValueError("auth_audience must include at least one audience identifier.")

        return list(dict.fromkeys(items))  # preserve order while deduplicating

    @field_validator("auth_key_storage_backend")
    @classmethod
    def _validate_key_storage_backend(cls, value: str) -> str:
        allowed = {"file", "secret-manager"}
        lowered = value.strip().lower()
        if lowered not in allowed:
            raise ValueError(f"auth_key_storage_backend must be one of {sorted(allowed)}")
        return lowered

    @field_validator("auth_jwks_cache_seconds")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Configuration value must be greater than zero.")
        return value

    @field_validator("stripe_secret_key", "stripe_webhook_secret")
    @classmethod
    def _validate_stripe_keys(cls, value: str | None, info: ValidationInfo):
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            raise ValueError(f"{info.field_name} must be a non-empty string when set.")
        return trimmed

    @field_validator("stripe_product_price_map", mode="before")
    @classmethod
    def _parse_price_map(cls, value):  # type: ignore[override]
        if value is None or value == {}:
            return {}
        if isinstance(value, dict):
            return value

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return {}
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = cls._parse_price_map_csv(text)
            return parsed

        raise ValueError(
            "STRIPE_PRODUCT_PRICE_MAP must be a mapping, JSON string, or comma-delimited list."
        )

    @staticmethod
    def _parse_price_map_csv(text: str) -> dict[str, str]:
        parsed: dict[str, str] = {}
        for item in text.split(","):
            entry = item.strip()
            if not entry:
                continue
            if "=" in entry:
                key, price = entry.split("=", 1)
            elif ":" in entry:
                key, price = entry.split(":", 1)
            else:
                raise ValueError(
                    "Invalid STRIPE_PRODUCT_PRICE_MAP entry. Use key=value or JSON dict."
                )
            parsed[key] = price
        return parsed

    @field_validator("stripe_product_price_map")
    @classmethod
    def _validate_price_map(cls, value: dict[str, str]) -> dict[str, str]:
        cleaned: dict[str, str] = {}
        for plan_code, price_id in value.items():
            plan = str(plan_code).strip()
            price = str(price_id).strip()
            if not plan or not price:
                raise ValueError(
                    "Stripe product price map entries require non-empty plan codes and price IDs."
                )
            cleaned[plan] = price
        return cleaned

    @field_validator("signup_rate_limit_per_hour", "signup_default_trial_days")
    @classmethod
    def _validate_signup_ints(cls, value: int, info: ValidationInfo) -> int:
        if value < 0:
            raise ValueError(f"{info.field_name} must be greater than or equal to zero.")
        return value


# =============================================================================
# SETTINGS INSTANCE
# =============================================================================


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings instance.

    Uses LRU cache to ensure settings are loaded only once.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


def enforce_secret_overrides(settings: Settings, *, force: bool = False) -> None:
    """
    Ensure production environments do not run with placeholder secrets.
    """

    issues = settings.secret_warnings()
    if not issues:
        return
    if force or settings.should_enforce_secret_overrides():
        formatted = "; ".join(issues)
        raise RuntimeError(
            "Production environment cannot start with default secrets. "
            f"Fix the following: {formatted}"
        )
