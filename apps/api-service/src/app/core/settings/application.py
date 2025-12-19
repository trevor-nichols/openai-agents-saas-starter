"""Application-level configuration primitives."""
from __future__ import annotations

from urllib.parse import urlparse

from pydantic import BaseModel, Field, model_validator

from .base import SAFE_ENVIRONMENTS


class ApplicationSettingsMixin(BaseModel):
    """Metadata, runtime flags, and network policies."""

    app_name: str = Field(default="api-service", description="Application name")
    app_description: str = Field(
        default="api-service FastAPI microservice", description="Application description"
    )
    app_version: str = Field(default="1.0.0", description="Application version")
    app_public_url: str = Field(
        default="http://localhost:3000",
        description="Public base URL used when generating email links.",
        alias="APP_PUBLIC_URL",
    )
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(
        default="development",
        description="Deployment environment label (development, staging, production, etc.)",
        alias="ENVIRONMENT",
    )
    port: int = Field(default=8000, description="Server port")

    allowed_hosts: str = Field(
        default="localhost,localhost:8000,127.0.0.1,testserver,testclient",
        description=(
            "Trusted hosts for FastAPI TrustedHostMiddleware (comma-separated host[:port] entries)."
        ),
    )
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="CORS allowed origins (comma-separated)",
    )
    allowed_methods: str = Field(
        default="GET,POST,PUT,DELETE,OPTIONS", description="CORS allowed methods (comma-separated)"
    )
    allowed_headers: str = Field(default="*", description="CORS allowed headers (comma-separated)")
    log_level: str = Field(default="INFO", description="Logging level")
    use_test_fixtures: bool = Field(
        default=False,
        description=(
            "Expose deterministic seeding endpoints for local and CI test environments. "
            "Never enable in production."
        ),
        alias="USE_TEST_FIXTURES",
    )

    @model_validator(mode="before")
    @classmethod
    def _default_debug_from_environment(cls, values: dict[str, object]) -> dict[str, object]:
        # Derive debug automatically from environment when not explicitly set.
        debug = values.get("debug")
        environment = str(values.get("environment") or "").lower()
        if debug is None:
            values["debug"] = environment in SAFE_ENVIRONMENTS
        return values

    def get_allowed_hosts_list(self) -> list[str]:
        normalized_hosts: list[str] = []
        for host in self.allowed_hosts.split(","):
            candidate = host.strip()
            if candidate and candidate not in normalized_hosts:
                normalized_hosts.append(candidate)

        if self.debug or self.environment.lower() in SAFE_ENVIRONMENTS:
            for safe_host in ("testserver", "testclient"):
                if safe_host not in normalized_hosts:
                    normalized_hosts.append(safe_host)

        if not normalized_hosts:
            normalized_hosts = ["localhost"]

        return normalized_hosts

    def get_allowed_origins_list(self) -> list[str]:
        origins: list[str] = []

        def _append_origin(raw: str | None) -> None:
            if not raw:
                return
            parsed = urlparse(raw.strip())
            candidate = raw.strip()
            if parsed.scheme and parsed.netloc:
                candidate = f"{parsed.scheme}://{parsed.netloc}"
            if candidate and candidate not in origins:
                origins.append(candidate)

        for origin in self.allowed_origins.split(","):
            _append_origin(origin)

        # Ensure the primary frontend URL is always allowed for CORS.
        _append_origin(self.app_public_url)

        return origins

    def get_allowed_methods_list(self) -> list[str]:
        return [method.strip() for method in self.allowed_methods.split(",") if method.strip()]

    def get_allowed_headers_list(self) -> list[str]:
        return [header.strip() for header in self.allowed_headers.split(",") if header.strip()]
