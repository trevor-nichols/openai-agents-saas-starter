# File: app/core/config.py
# Purpose: Configuration management for anything-agents
# Dependencies: pydantic-settings, python-dotenv
# Used by: main.py and other modules requiring configuration

from functools import lru_cache

from pydantic import Field, field_validator


from pydantic_settings import BaseSettings

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
        default="anything-agents FastAPI microservice",
        description="Application description"
    )
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
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
    
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    
    # =============================================================================
    # REDIS SETTINGS
    # =============================================================================
    
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # =============================================================================
    # CORS SETTINGS (simplified to avoid parsing issues)
    # =============================================================================
    
    allowed_origins: str = Field(
        default="http://localhost:8000,http://localhost:8080",
        description="CORS allowed origins (comma-separated)"
    )
    allowed_methods: str = Field(
        default="GET,POST,PUT,DELETE,OPTIONS",
        description="CORS allowed methods (comma-separated)"
    )
    allowed_headers: str = Field(
        default="*",
        description="CORS allowed headers (comma-separated)"
    )

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
            "Provide as JSON array via AUTH_AUDIENCE environment variable; comma-separated strings are accepted when instantiating Settings directly."
        ),
    )
    auth_key_storage_backend: str = Field(
        default="file",
        description="Key storage backend (file or secret-manager).",
    )
    auth_key_storage_path: str = Field(
        default="var/keys/keyset.json",
        description="Filesystem path for keyset JSON when using file backend.",
    )
    auth_key_secret_name: str | None = Field(
        default=None,
        description="Secret-manager key/path storing keyset JSON when backend=secret-manager.",
    )
    auth_jwks_cache_seconds: int = Field(
        default=300,
        description="Cache max-age for /.well-known/jwks.json responses.",
    )
    auth_rotation_overlap_minutes: int = Field(
        default=1440,
        description="Maximum minutes between active and next key creation timestamps.",
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
    use_in_memory_repo: bool = Field(
        default=True,
        description="Use in-memory repositories instead of Postgres (development defaults)",
    )
    enable_billing: bool = Field(
        default=False,
        description="Expose billing features and APIs once subscriptions are implemented",
    )
    auto_run_migrations: bool = Field(
        default=False,
        description="Automatically run Alembic migrations on startup (dev convenience)",
    )
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def get_allowed_origins_list(self) -> list[str]:
        """Get allowed origins as a list."""
        return [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]
    
    def get_allowed_methods_list(self) -> list[str]:
        """Get allowed methods as a list."""
        return [method.strip() for method in self.allowed_methods.split(',') if method.strip()]
    
    def get_allowed_headers_list(self) -> list[str]:
        """Get allowed headers as a list."""
        return [header.strip() for header in self.allowed_headers.split(',') if header.strip()]
    
    # =============================================================================
    # CONFIGURATION
    # =============================================================================
    
    model_config = {
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
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
        elif isinstance(value, (list, tuple, set)):
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

    @field_validator("auth_jwks_cache_seconds", "auth_rotation_overlap_minutes")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Configuration value must be greater than zero.")
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
