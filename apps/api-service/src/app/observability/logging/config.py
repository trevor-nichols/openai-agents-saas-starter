"""Logging configuration assembly for dictConfig."""

from __future__ import annotations

from starter_contracts.observability.logging import LoggingRuntimeConfig
from starter_contracts.observability.logging.config import (
    ALLOWED_SINKS as SHARED_ALLOWED_SINKS,
    configure_logging as configure_shared_logging,
)

from app.core import paths as core_paths
from app.core.settings import Settings


def configure_logging(settings: Settings) -> None:
    """Apply JSON logging configuration based on deployment settings."""

    runtime = LoggingRuntimeConfig(
        service=settings.app_name,
        environment=settings.environment,
        log_level=settings.log_level,
        logging_sinks=settings.logging_sinks,
        log_root=settings.log_root,
        logging_file_path=settings.logging_file_path,
        logging_file_max_mb=settings.logging_file_max_mb,
        logging_file_backups=settings.logging_file_backups,
        logging_max_days=settings.logging_max_days,
        logging_duplex_error_file=settings.logging_duplex_error_file,
        logging_datadog_api_key=settings.logging_datadog_api_key,
        logging_datadog_site=settings.logging_datadog_site,
        logging_otlp_endpoint=settings.logging_otlp_endpoint,
        logging_otlp_headers=settings.logging_otlp_headers,
        component="api",
        handler_namespace="app.observability.logging.sinks",
        default_file_path="var/log/api-service.log",
        repo_root=core_paths.REPO_ROOT,
    )
    configure_shared_logging(runtime)


ALLOWED_SINKS = SHARED_ALLOWED_SINKS

__all__ = ["ALLOWED_SINKS", "configure_logging"]
