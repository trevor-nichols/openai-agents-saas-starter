"""Observability, logging sinks, and GeoIP providers."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ObservabilitySettingsMixin(BaseModel):
    logging_sink: str = Field(
        default="stdout",
        description="Logging sink (stdout, file, datadog, otlp, or none).",
        alias="LOGGING_SINK",
    )
    logging_file_path: str = Field(
        default="var/log/api-service.log",
        description="Filesystem path for file sink when logging_sink=file.",
        alias="LOGGING_FILE_PATH",
    )
    logging_file_max_mb: int = Field(
        default=10,
        ge=1,
        description="Maximum megabytes per log file when logging_sink=file.",
        alias="LOGGING_FILE_MAX_MB",
    )
    logging_file_backups: int = Field(
        default=5,
        ge=0,
        description="Rotated backup files to retain when logging_sink=file.",
        alias="LOGGING_FILE_BACKUPS",
    )
    enable_frontend_log_ingest: bool = Field(
        default=False,
        description="Expose authenticated frontend log ingest endpoint.",
        alias="ENABLE_FRONTEND_LOG_INGEST",
    )
    logging_datadog_api_key: str | None = Field(
        default=None,
        description="Datadog API key when logging_sink=datadog.",
        alias="LOGGING_DATADOG_API_KEY",
    )
    logging_datadog_site: str | None = Field(
        default="datadoghq.com",
        description="Datadog site (datadoghq.com, datadoghq.eu, etc.).",
        alias="LOGGING_DATADOG_SITE",
    )
    logging_otlp_endpoint: str | None = Field(
        default=None,
        description="OTLP/HTTP endpoint when logging_sink=otlp.",
        alias="LOGGING_OTLP_ENDPOINT",
    )
    logging_otlp_headers: str | None = Field(
        default=None,
        description="Optional OTLP headers JSON when logging_sink=otlp.",
        alias="LOGGING_OTLP_HEADERS",
    )
    geoip_provider: str = Field(
        default="none",
        description=(
            "GeoIP provider selection (none, ipinfo, ip2location, maxmind_db, "
            "ip2location_db)."
        ),
        alias="GEOIP_PROVIDER",
    )
    geoip_ipinfo_token: str | None = Field(
        default=None,
        description="IPinfo API token when geoip_provider=ipinfo.",
        alias="GEOIP_IPINFO_TOKEN",
    )
    geoip_maxmind_license_key: str | None = Field(
        default=None,
        description="MaxMind license key when geoip_provider=maxmind.",
        alias="GEOIP_MAXMIND_LICENSE_KEY",
    )
    geoip_maxmind_db_path: str | None = Field(
        default=None,
        description="Filesystem path to the MaxMind GeoIP2/GeoLite2 database.",
        alias="GEOIP_MAXMIND_DB_PATH",
    )
    geoip_ip2location_api_key: str | None = Field(
        default=None,
        description="IP2Location API key when geoip_provider=ip2location.",
        alias="GEOIP_IP2LOCATION_API_KEY",
    )
    geoip_ip2location_db_path: str | None = Field(
        default=None,
        description="Filesystem path to the IP2Location BIN database.",
        alias="GEOIP_IP2LOCATION_DB_PATH",
    )
    geoip_cache_ttl_seconds: float = Field(
        default=900.0,
        ge=0.0,
        description="TTL (seconds) for GeoIP lookup cache entries.",
        alias="GEOIP_CACHE_TTL_SECONDS",
    )
    geoip_cache_max_entries: int = Field(
        default=4096,
        ge=1,
        description="Maximum cached GeoIP lookups to retain in memory.",
        alias="GEOIP_CACHE_MAX_ENTRIES",
    )
    geoip_http_timeout_seconds: float = Field(
        default=2.0,
        gt=0.0,
        description="HTTP timeout (seconds) for SaaS GeoIP providers.",
        alias="GEOIP_HTTP_TIMEOUT_SECONDS",
    )
