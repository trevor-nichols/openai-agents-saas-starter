from __future__ import annotations

from pathlib import Path

from starter_cli.cli.common import CLIError
from starter_cli.cli.console import console
from starter_cli.cli.setup._wizard.context import WizardContext
from starter_cli.cli.setup.automation import AutomationPhase, AutomationStatus
from starter_cli.cli.setup.geoip import download_maxmind_database
from starter_cli.cli.setup.inputs import InputProvider
from starter_cli.cli.setup.validators import normalize_geoip_provider, normalize_logging_sink


def run(context: WizardContext, provider: InputProvider) -> None:
    console.info("[M3] Tenant & Observability", topic="wizard")
    slug = provider.prompt_string(
        key="TENANT_DEFAULT_SLUG",
        prompt="Default tenant slug",
        default=context.current("TENANT_DEFAULT_SLUG") or "default",
        required=True,
    )
    context.set_backend("TENANT_DEFAULT_SLUG", slug)

    sink = normalize_logging_sink(
        provider.prompt_string(
            key="LOGGING_SINK",
            prompt="Logging sink (stdout/datadog/otlp/none)",
            default=context.current("LOGGING_SINK") or "stdout",
            required=True,
        )
    )
    context.set_backend("LOGGING_SINK", sink)
    if sink == "datadog":
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
    elif sink == "otlp":
        endpoint = provider.prompt_string(
            key="LOGGING_OTLP_ENDPOINT",
            prompt="OTLP/HTTP endpoint",
            default=context.current("LOGGING_OTLP_ENDPOINT") or "https://collector.example/v1/logs",
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

    geo = normalize_geoip_provider(
        provider.prompt_string(
            key="GEOIP_PROVIDER",
            prompt="GeoIP provider (none/ipinfo/ip2location/maxmind_db/ip2location_db)",
            default=context.current("GEOIP_PROVIDER") or "none",
            required=True,
        )
    )
    context.set_backend("GEOIP_PROVIDER", geo)
    if context.profile != "local" and geo == "none":
        console.warn(
            (
                "GeoIP provider is disabled for a non-local profile; session telemetry "
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
    http_timeout = provider.prompt_string(
        key="GEOIP_HTTP_TIMEOUT_SECONDS",
        prompt="GeoIP HTTP timeout (seconds)",
        default=context.current("GEOIP_HTTP_TIMEOUT_SECONDS") or "2.0",
        required=True,
    )
    context.set_backend("GEOIP_HTTP_TIMEOUT_SECONDS", http_timeout)


def _maybe_download_maxmind_db(
    context: WizardContext,
    provider: InputProvider,
    *,
    license_key: str,
    raw_path: str,
) -> None:
    target = _resolve_geoip_path(context, raw_path)
    default_download = context.profile != "local"
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
                download_maxmind_database(license_key=license_key, target_path=target)
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
        _warn_missing_path(target, label="MaxMind database")
        return
    try:
        download_maxmind_database(license_key=license_key, target_path=target)
    except CLIError as exc:
        console.error(f"Failed to download MaxMind database: {exc}", topic="geoip")
        _warn_missing_path(target, label="MaxMind database")


def _warn_missing_db(context: WizardContext, raw_path: str, *, provider_name: str) -> None:
    target = _resolve_geoip_path(context, raw_path)
    _warn_missing_path(target, label=f"{provider_name} database")


def _resolve_geoip_path(context: WizardContext, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (context.cli_ctx.project_root / candidate).resolve()


def _warn_missing_path(path: Path, *, label: str) -> None:
    if path.exists():
        return
    console.warn(
        f"{label} not found at {path}. Download it now or update the path later.",
        topic="geoip",
    )
