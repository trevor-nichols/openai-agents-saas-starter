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

    sink_prompt_default = context.policy_env_default("LOGGING_SINKS", fallback="stdout")
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
            default=context.policy_env_default(
                "LOGGING_FILE_PATH", fallback="var/log/api-service.log"
            ),
            required=True,
        )
        max_mb = provider.prompt_string(
            key="LOGGING_FILE_MAX_MB",
            prompt="Max file size (MB)",
            default=context.policy_env_default("LOGGING_FILE_MAX_MB", fallback="10"),
            required=True,
        )
        backups = provider.prompt_string(
            key="LOGGING_FILE_BACKUPS",
            prompt="Number of rotated backups to keep",
            default=context.policy_env_default("LOGGING_FILE_BACKUPS", fallback="5"),
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
            default=context.policy_env_default("LOGGING_DATADOG_SITE", fallback="datadoghq.com"),
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
            default=context.policy_env_default(
                "LOGGING_OTLP_ENDPOINT",
                fallback=(
                    "http://otel-collector:4318/v1/logs"
                    if use_bundled_collector
                    else "https://collector.example/v1/logs"
                ),
            ),
            required=True,
        )
        headers = provider.prompt_string(
            key="LOGGING_OTLP_HEADERS",
            prompt="OTLP headers JSON (optional)",
            default=context.policy_env_default("LOGGING_OTLP_HEADERS", fallback=""),
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

    ingest_default = context.policy_env_default_bool("ENABLE_FRONTEND_LOG_INGEST", fallback=False)
    ingest_enabled = provider.prompt_bool(
        key="ENABLE_FRONTEND_LOG_INGEST",
        prompt="Accept authenticated frontend logs at /api/v1/logs?",
        default=ingest_default,
    )
    if ingest_enabled and context.policy_rule_bool(
        "frontend_log_ingest_requires_confirmation", fallback=False
    ):
        console.warn(
            (
                "Frontend log ingest is enabled for production. Ensure you have approved "
                "retention rules and a PII redaction/collection policy before proceeding."
            ),
            topic="frontend-logging",
        )
        confirmed = provider.prompt_bool(
            key="CONFIRM_ENABLE_FRONTEND_LOG_INGEST",
            prompt="Confirm production frontend log ingest is approved?",
            default=False,
        )
        if not confirmed:
            console.warn(
                (
                    "Production frontend log ingest not confirmed; disabling "
                    "ENABLE_FRONTEND_LOG_INGEST."
                ),
                topic="frontend-logging",
            )
            ingest_enabled = False
    context.set_backend_bool("ENABLE_FRONTEND_LOG_INGEST", ingest_enabled)

    geo = normalize_geoip_provider(
        provider.prompt_string(
            key="GEOIP_PROVIDER",
            prompt="GeoIP provider (none/ipinfo/ip2location/maxmind_db/ip2location_db)",
            default=context.policy_env_default("GEOIP_PROVIDER", fallback="none"),
            required=True,
        )
    )
    context.set_backend("GEOIP_PROVIDER", geo)
    geo_mode = context.policy_rule_str("geoip_required_mode", fallback="disabled")
    if geo_mode != "disabled" and geo == "none":
        console.warn(
            (
                "GeoIP provider is disabled while the profile policy expects telemetry; "
                "session telemetry will lack location data."
            ),
            topic="geoip",
        )
        if geo_mode == "error":
            raise CLIError("GeoIP provider is required by profile policy.")
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
            default=context.policy_env_default(
                "GEOIP_MAXMIND_DB_PATH", fallback="var/geoip/GeoLite2-City.mmdb"
            ),
            required=True,
        )
        context.set_backend("GEOIP_MAXMIND_DB_PATH", db_path)
        _maybe_download_maxmind_db(context, provider, license_key=license_key, raw_path=db_path)
    elif geo == "ip2location_db":
        default_ip2location = "var/geoip/IP2LOCATION-LITE-DB3.BIN"
        db_path = provider.prompt_string(
            key="GEOIP_IP2LOCATION_DB_PATH",
            prompt="Path to IP2Location BIN database",
            default=context.policy_env_default(
                "GEOIP_IP2LOCATION_DB_PATH", fallback=default_ip2location
            ),
            required=True,
        )
        context.set_backend("GEOIP_IP2LOCATION_DB_PATH", db_path)
        _warn_missing_db(context, db_path, provider_name="IP2Location")

    cache_ttl = provider.prompt_string(
        key="GEOIP_CACHE_TTL_SECONDS",
        prompt="GeoIP cache TTL (seconds)",
        default=context.policy_env_default("GEOIP_CACHE_TTL_SECONDS", fallback="900"),
        required=True,
    )
    context.set_backend("GEOIP_CACHE_TTL_SECONDS", cache_ttl)
    cache_max = provider.prompt_string(
        key="GEOIP_CACHE_MAX_ENTRIES",
        prompt="GeoIP cache capacity (entries)",
        default=context.policy_env_default("GEOIP_CACHE_MAX_ENTRIES", fallback="4096"),
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
        default=context.policy_env_default("GEOIP_HTTP_TIMEOUT_SECONDS", fallback="2.0"),
        required=True,
    )
    context.set_backend("GEOIP_HTTP_TIMEOUT_SECONDS", http_timeout)


def _collector_default(context: WizardContext) -> bool:
    return context.policy_env_default_bool("ENABLE_OTEL_COLLECTOR", fallback=False)


def _clear_collector_exporters(context: WizardContext) -> None:
    context.unset_backend("OTEL_EXPORTER_SENTRY_ENDPOINT")
    context.unset_backend("OTEL_EXPORTER_SENTRY_AUTH_HEADER")
    context.unset_backend("OTEL_EXPORTER_SENTRY_HEADERS")


def _configure_collector_exporters(context: WizardContext, provider: InputProvider) -> None:
    _configure_sentry_exporter(context, provider)


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
        default=context.policy_env_default(
            "OTEL_EXPORTER_SENTRY_ENDPOINT",
            fallback="https://o11y.ingest.sentry.io/api/<project>/otlp",
        ),
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
        default=context.policy_env_default("OTEL_EXPORTER_SENTRY_HEADERS", fallback=""),
        required=False,
    )
    context.set_backend("OTEL_EXPORTER_SENTRY_ENDPOINT", endpoint)
    context.set_backend("OTEL_EXPORTER_SENTRY_AUTH_HEADER", auth_header, mask=True)
    if headers:
        context.set_backend("OTEL_EXPORTER_SENTRY_HEADERS", headers)
    else:
        context.unset_backend("OTEL_EXPORTER_SENTRY_HEADERS")


def _maybe_download_maxmind_db(
    context: WizardContext,
    provider: InputProvider,
    *,
    license_key: str,
    raw_path: str,
) -> None:
    if context.skip_external_calls:
        context.console.info(
            "Skipping GeoIP database download (external calls disabled).",
            topic="geoip",
        )
        return
    console = context.console
    target = _resolve_geoip_path(context, raw_path)
    mode = context.policy_rule_str("geoip_required_mode", fallback="disabled")
    default_download = mode in {"warn", "error"}
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
