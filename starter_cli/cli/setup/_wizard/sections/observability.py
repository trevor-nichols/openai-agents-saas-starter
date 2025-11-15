from __future__ import annotations

from starter_cli.cli.console import console
from starter_cli.cli.setup._wizard.context import WizardContext
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
            prompt="GeoIP provider (none/maxmind/ip2location)",
            default=context.current("GEOIP_PROVIDER") or "none",
            required=True,
        )
    )
    context.set_backend("GEOIP_PROVIDER", geo)
    if geo == "maxmind":
        license_key = provider.prompt_secret(
            key="GEOIP_MAXMIND_LICENSE_KEY",
            prompt="MaxMind license key",
            existing=context.current("GEOIP_MAXMIND_LICENSE_KEY"),
            required=True,
        )
        context.set_backend("GEOIP_MAXMIND_LICENSE_KEY", license_key, mask=True)
    elif geo == "ip2location":
        api_key = provider.prompt_secret(
            key="GEOIP_IP2LOCATION_API_KEY",
            prompt="IP2Location API key",
            existing=context.current("GEOIP_IP2LOCATION_API_KEY"),
            required=True,
        )
        context.set_backend("GEOIP_IP2LOCATION_API_KEY", api_key, mask=True)
