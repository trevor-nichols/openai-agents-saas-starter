from __future__ import annotations

from pathlib import Path

from starter_console.core import CLIError

from ...automation import AutomationPhase, AutomationStatus
from ...geoip import download_maxmind_database
from ...inputs import InputProvider
from ...validators import (
    normalize_geoip_provider,
    normalize_logging_sinks,
    parse_non_negative_int,
    parse_positive_int,
)
from ..context import WizardContext


def run(context: WizardContext, provider: InputProvider) -> None:
    console = context.console
    console.section(
        "Tenant & Observability",
        "Name the default tenant and configure logging, GeoIP, and monitoring sinks.",
    )
    slug = provider.prompt_string(
        key="TENANT_DEFAULT_SLUG",
        prompt="Default tenant slug",
        default=context.current("TENANT_DEFAULT_SLUG") or "default",
        required=True,
    )
    context.set_backend("TENANT_DEFAULT_SLUG", slug)

    sink_prompt_default = context.current("LOGGING_SINKS") or "stdout"
    sinks = normalize_logging_sinks(
        provider.prompt_string(
            key="LOGGING_SINKS",
            prompt="Logging sinks (comma-separated: stdout/file/datadog/otlp/none)",
            default=sink_prompt_default,
            required=True,
        )
    )

    context.set_backend("LOGGING_SINKS", ",".join(sinks))

    sink_set = set(sinks)
    context.set_backend_bool("LOGGING_SINK_HAS_FILE", "file" in sink_set)
    context.set_backend_bool("LOGGING_SINK_HAS_DATADOG", "datadog" in sink_set)
    context.set_backend_bool("LOGGING_SINK_HAS_OTLP", "otlp" in sink_set)
    if "file" in sink_set:
        log_path = provider.prompt_string(
            key="LOGGING_FILE_PATH",
            prompt="Log file path (rotating)",
            default=context.current("LOGGING_FILE_PATH") or "var/log/api-service.log",
            required=True,
        )
        max_mb = provider.prompt_string(
            key="LOGGING_FILE_MAX_MB",
            prompt="Max file size (MB)",
            default=context.current("LOGGING_FILE_MAX_MB") or "10",
            required=True,
        )
        backups = provider.prompt_string(
            key="LOGGING_FILE_BACKUPS",
            prompt="Number of rotated backups to keep",
            default=context.current("LOGGING_FILE_BACKUPS") or "5",
            required=True,
        )
        context.set_backend("LOGGING_FILE_PATH", log_path)
        context.set_backend(
            "LOGGING_FILE_MAX_MB",
            str(parse_positive_int(max_mb, field="LOGGING_FILE_MAX_MB", minimum=1)),
        )
        context.set_backend(
            "LOGGING_FILE_BACKUPS",
            str(parse_non_negative_int(backups, field="LOGGING_FILE_BACKUPS")),
        )
    if "datadog" in sink_set:
        api_key = provider.prompt_secret(
            key="LOGGING_DATADOG_API_KEY",
            prompt="Datadog API key",
            existing=context.current("LOGGING_DATADOG_API_KEY"),
            required=True,
        )
        site = provider.prompt_string(
            key="LOGGING_DATADOG_SITE",
            prompt="Datadog site (e.g., datadoghq.com)",
            default=context.current("LOGGING_DATADOG_SITE") or "datadoghq.com",
            required=True,
        )
        context.set_backend("LOGGING_DATADOG_API_KEY", api_key, mask=True)
        context.set_backend("LOGGING_DATADOG_SITE", site)
    if "otlp" in sink_set:
        bundled_default = _collector_default(context)
        use_bundled_collector = provider.prompt_bool(
            key="ENABLE_OTEL_COLLECTOR",
            prompt="Start bundled OpenTelemetry Collector via docker compose?",
            default=bundled_default,
        )
        context.set_backend_bool("ENABLE_OTEL_COLLECTOR", use_bundled_collector)
        endpoint = provider.prompt_string(
            key="LOGGING_OTLP_ENDPOINT",
            prompt="OTLP/HTTP endpoint",
            default=
            context.current("LOGGING_OTLP_ENDPOINT")
            or (
                "http://otel-collector:4318/v1/logs"
                if use_bundled_collector
                else "https://collector.example/v1/logs"
            ),
            required=True,
        )
        headers = provider.prompt_string(
            key="LOGGING_OTLP_HEADERS",
            prompt="OTLP headers JSON (optional)",
            default=context.current("LOGGING_OTLP_HEADERS") or "",
            required=False,
        )
        context.set_backend("LOGGING_OTLP_ENDPOINT", endpoint)
        if headers:
            context.set_backend("LOGGING_OTLP_HEADERS", headers)
        else:
            context.unset_backend("LOGGING_OTLP_HEADERS")
        if use_bundled_collector:
            _configure_collector_exporters(context, provider)
        else:
            _clear_collector_exporters(context)
    if "otlp" not in sink_set:
        context.set_backend_bool("ENABLE_OTEL_COLLECTOR", False)
        _clear_collector_exporters(context)

    ingest_enabled = provider.prompt_bool(
        key="ENABLE_FRONTEND_LOG_INGEST",
        prompt="Accept authenticated frontend logs at /api/v1/logs?",
        default=context.current_bool("ENABLE_FRONTEND_LOG_INGEST", False),
    )
    context.set_backend_bool("ENABLE_FRONTEND_LOG_INGEST", ingest_enabled)

    geo = normalize_geoip_provider(
        provider.prompt_string(
            key="GEOIP_PROVIDER",
            prompt="GeoIP provider (none/ipinfo/ip2location/maxmind_db/ip2location_db)",
            default=context.current("GEOIP_PROVIDER") or "none",
            required=True,
        )
    )
    context.set_backend("GEOIP_PROVIDER", geo)
    if context.profile != "demo" and geo == "none":
        console.warn(
            (
                "GeoIP provider is disabled for a non-demo profile; session telemetry "
                "will lack location data."
            ),
            topic="geoip",
        )
    if geo == "ipinfo":
        token = provider.prompt_secret(
            key="GEOIP_IPINFO_TOKEN",
            prompt="IPinfo API token",
            existing=context.current("GEOIP_IPINFO_TOKEN"),
            required=True,
        )
        context.set_backend("GEOIP_IPINFO_TOKEN", token, mask=True)
    elif geo == "ip2location":
        api_key = provider.prompt_secret(
            key="GEOIP_IP2LOCATION_API_KEY",
            prompt="IP2Location API key",
            existing=context.current("GEOIP_IP2LOCATION_API_KEY"),
            required=True,
        )
        context.set_backend("GEOIP_IP2LOCATION_API_KEY", api_key, mask=True)
    elif geo == "maxmind_db":
        license_key = provider.prompt_secret(
            key="GEOIP_MAXMIND_LICENSE_KEY",
            prompt="MaxMind license key",
            existing=context.current("GEOIP_MAXMIND_LICENSE_KEY"),
            required=True,
        )
        context.set_backend("GEOIP_MAXMIND_LICENSE_KEY", license_key, mask=True)
        db_path = provider.prompt_string(
            key="GEOIP_MAXMIND_DB_PATH",
            prompt="Path to MaxMind GeoIP database",
            default=context.current("GEOIP_MAXMIND_DB_PATH") or "var/geoip/GeoLite2-City.mmdb",
            required=True,
        )
        context.set_backend("GEOIP_MAXMIND_DB_PATH", db_path)
        _maybe_download_maxmind_db(context, provider, license_key=license_key, raw_path=db_path)
    elif geo == "ip2location_db":
        default_ip2location = "var/geoip/IP2LOCATION-LITE-DB3.BIN"
        db_path = provider.prompt_string(
            key="GEOIP_IP2LOCATION_DB_PATH",
            prompt="Path to IP2Location BIN database",
            default=context.current("GEOIP_IP2LOCATION_DB_PATH") or default_ip2location,
            required=True,
        )
        context.set_backend("GEOIP_IP2LOCATION_DB_PATH", db_path)
        _warn_missing_db(context, db_path, provider_name="IP2Location")

    cache_ttl = provider.prompt_string(
        key="GEOIP_CACHE_TTL_SECONDS",
        prompt="GeoIP cache TTL (seconds)",
        default=context.current("GEOIP_CACHE_TTL_SECONDS") or "900",
        required=True,
    )
    context.set_backend("GEOIP_CACHE_TTL_SECONDS", cache_ttl)
    cache_max = provider.prompt_string(
        key="GEOIP_CACHE_MAX_ENTRIES",
        prompt="GeoIP cache capacity (entries)",
        default=context.current("GEOIP_CACHE_MAX_ENTRIES") or "4096",
        required=True,
    )
    context.set_backend("GEOIP_CACHE_MAX_ENTRIES", cache_max)

    # Helper flags used for schema gating; avoid persisting them to .env
    context.unset_backend("LOGGING_SINK_HAS_FILE")
    context.unset_backend("LOGGING_SINK_HAS_DATADOG")
    context.unset_backend("LOGGING_SINK_HAS_OTLP")
    http_timeout = provider.prompt_string(
        key="GEOIP_HTTP_TIMEOUT_SECONDS",
        prompt="GeoIP HTTP timeout (seconds)",
        default=context.current("GEOIP_HTTP_TIMEOUT_SECONDS") or "2.0",
        required=True,
    )
    context.set_backend("GEOIP_HTTP_TIMEOUT_SECONDS", http_timeout)


def _collector_default(context: WizardContext) -> bool:
    current = context.current("ENABLE_OTEL_COLLECTOR")
    if current is not None:
        return context.current_bool("ENABLE_OTEL_COLLECTOR")
    return context.profile == "demo"


def _clear_collector_exporters(context: WizardContext) -> None:
    context.unset_backend("OTEL_EXPORTER_SENTRY_ENDPOINT")
    context.unset_backend("OTEL_EXPORTER_SENTRY_AUTH_HEADER")
    context.unset_backend("OTEL_EXPORTER_SENTRY_HEADERS")
    context.unset_backend("OTEL_EXPORTER_DATADOG_API_KEY")
    context.unset_backend("OTEL_EXPORTER_DATADOG_SITE")


def _configure_collector_exporters(context: WizardContext, provider: InputProvider) -> None:
    _configure_sentry_exporter(context, provider)
    _configure_datadog_exporter(context, provider)


def _configure_sentry_exporter(context: WizardContext, provider: InputProvider) -> None:
    default_enabled = bool(context.current("OTEL_EXPORTER_SENTRY_ENDPOINT"))
    enabled = provider.prompt_bool(
        key="OTEL_EXPORTER_SENTRY_ENABLED",
        prompt="Forward logs to Sentry from the bundled collector?",
        default=default_enabled,
    )
    if not enabled:
        context.unset_backend("OTEL_EXPORTER_SENTRY_ENDPOINT")
        context.unset_backend("OTEL_EXPORTER_SENTRY_AUTH_HEADER")
        context.unset_backend("OTEL_EXPORTER_SENTRY_HEADERS")
        return
    endpoint = provider.prompt_string(
        key="OTEL_EXPORTER_SENTRY_ENDPOINT",
        prompt="Sentry OTLP HTTP endpoint",
        default=context.current("OTEL_EXPORTER_SENTRY_ENDPOINT")
        or "https://o11y.ingest.sentry.io/api/<project>/otlp",
        required=True,
    )
    auth_header = provider.prompt_secret(
        key="OTEL_EXPORTER_SENTRY_AUTH_HEADER",
        prompt="Sentry Authorization header (e.g., 'Bearer <token>')",
        existing=context.current("OTEL_EXPORTER_SENTRY_AUTH_HEADER"),
        required=True,
    )
    headers = provider.prompt_string(
        key="OTEL_EXPORTER_SENTRY_HEADERS",
        prompt="Additional Sentry headers JSON (optional)",
        default=context.current("OTEL_EXPORTER_SENTRY_HEADERS") or "",
        required=False,
    )
    context.set_backend("OTEL_EXPORTER_SENTRY_ENDPOINT", endpoint)
    context.set_backend("OTEL_EXPORTER_SENTRY_AUTH_HEADER", auth_header, mask=True)
    if headers:
        context.set_backend("OTEL_EXPORTER_SENTRY_HEADERS", headers)
    else:
        context.unset_backend("OTEL_EXPORTER_SENTRY_HEADERS")


def _configure_datadog_exporter(context: WizardContext, provider: InputProvider) -> None:
    default_enabled = bool(context.current("OTEL_EXPORTER_DATADOG_API_KEY"))
    enabled = provider.prompt_bool(
        key="OTEL_EXPORTER_DATADOG_ENABLED",
        prompt="Forward logs to Datadog from the bundled collector?",
        default=default_enabled,
    )
    if not enabled:
        context.unset_backend("OTEL_EXPORTER_DATADOG_API_KEY")
        context.unset_backend("OTEL_EXPORTER_DATADOG_SITE")
        return
    api_key = provider.prompt_secret(
        key="OTEL_EXPORTER_DATADOG_API_KEY",
        prompt="Datadog API key",
        existing=context.current("OTEL_EXPORTER_DATADOG_API_KEY"),
        required=True,
    )
    site = provider.prompt_string(
        key="OTEL_EXPORTER_DATADOG_SITE",
        prompt="Datadog site (datadoghq.com/datadoghq.eu/etc.)",
        default=context.current("OTEL_EXPORTER_DATADOG_SITE") or "datadoghq.com",
        required=True,
    )
    context.set_backend("OTEL_EXPORTER_DATADOG_API_KEY", api_key, mask=True)
    context.set_backend("OTEL_EXPORTER_DATADOG_SITE", site)


def _maybe_download_maxmind_db(
    context: WizardContext,
    provider: InputProvider,
    *,
    license_key: str,
    raw_path: str,
) -> None:
    console = context.console
    target = _resolve_geoip_path(context, raw_path)
    default_download = context.profile != "demo"
    record = context.automation.get(AutomationPhase.GEOIP)
    if record.enabled:
        if record.status == AutomationStatus.BLOCKED:
            console.warn(record.note or "GeoIP automation blocked.", topic="geoip")
            context.refresh_automation_ui(AutomationPhase.GEOIP)
        else:
            context.automation.update(
                AutomationPhase.GEOIP,
                AutomationStatus.RUNNING,
                f"Downloading GeoIP DB to {raw_path}",
            )
            context.refresh_automation_ui(AutomationPhase.GEOIP)
            try:
                download_maxmind_database(
                    license_key=license_key,
                    target_path=target,
                    console=console,
                )
            except CLIError as exc:
                context.automation.update(
                    AutomationPhase.GEOIP,
                    AutomationStatus.FAILED,
                    f"GeoIP download failed: {exc}",
                )
                context.refresh_automation_ui(AutomationPhase.GEOIP)
                raise
            else:
                context.automation.update(
                    AutomationPhase.GEOIP,
                    AutomationStatus.SUCCEEDED,
                    "GeoIP database downloaded.",
                )
                context.refresh_automation_ui(AutomationPhase.GEOIP)
            return
    should_download = provider.prompt_bool(
        key="GEOIP_MAXMIND_DOWNLOAD",
        prompt=f"Download/refresh MaxMind DB at {raw_path} now?",
        default=default_download,
    )
    if not should_download:
        _warn_missing_path(console, target, label="MaxMind database")
        return
    try:
        download_maxmind_database(
            license_key=license_key,
            target_path=target,
            console=console,
        )
    except CLIError as exc:
        console.error(f"Failed to download MaxMind database: {exc}", topic="geoip")
        _warn_missing_path(console, target, label="MaxMind database")


def _warn_missing_db(context: WizardContext, raw_path: str, *, provider_name: str) -> None:
    target = _resolve_geoip_path(context, raw_path)
    _warn_missing_path(context.console, target, label=f"{provider_name} database")


def _resolve_geoip_path(context: WizardContext, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (context.cli_ctx.project_root / candidate).resolve()


def _warn_missing_path(console, path: Path, *, label: str) -> None:
    if path.exists():
        return
    console.warn(
        f"{label} not found at {path}. Download it now or update the path later.",
        topic="geoip",
    )
