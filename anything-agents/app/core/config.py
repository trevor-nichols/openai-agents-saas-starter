# File: app/core/config.py
# Purpose: Configuration management for anything-agents
# Dependencies: pydantic-settings, python-dotenv
# Used by: main.py and other modules requiring configuration

from functools import lru_cache

from pydantic import Field
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
    # LOGGING SETTINGS
    # =============================================================================
    
    log_level: str = Field(default="INFO", description="Logging level")

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
