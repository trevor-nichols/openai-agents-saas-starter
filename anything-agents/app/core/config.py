# File: app/core/config.py
# Purpose: Configuration management for anything-agents
# Dependencies: pydantic-settings, python-dotenv
# Used by: main.py and other modules requiring configuration

from functools import lru_cache
from typing import List, Optional

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
    
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    xai_api_key: Optional[str] = Field(default=None, description="xAI API key")
    
    # =============================================================================
    # AI TOOLS API KEYS
    # =============================================================================
    
    tavily_api_key: Optional[str] = Field(default=None, description="Tavily web search API key")
    
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
    # HELPER METHODS
    # =============================================================================
    
    def get_allowed_origins_list(self) -> List[str]:
        """Get allowed origins as a list."""
        return [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]
    
    def get_allowed_methods_list(self) -> List[str]:
        """Get allowed methods as a list."""
        return [method.strip() for method in self.allowed_methods.split(',') if method.strip()]
    
    def get_allowed_headers_list(self) -> List[str]:
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

@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings instance.
    
    Uses LRU cache to ensure settings are loaded only once.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings() 