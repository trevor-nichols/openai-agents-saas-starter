"""Pluggable GeoIP lookup services used by the auth session pipeline."""

from __future__ import annotations

import inspect
from typing import Protocol

from app.core.settings import Settings
from app.domain.auth import SessionLocation
from app.infrastructure.geoip.providers import (
    IP2LocationDatabaseService,
    IP2LocationHTTPService,
    IPinfoGeoIPService,
    MaxMindDBGeoIPService,
)


class GeoIPService(Protocol):
    """Async interface for translating IP addresses into coarse locations."""

    async def lookup(self, ip_address: str) -> SessionLocation | None: ...


class NullGeoIPService:
    """Default GeoIP implementation that always returns None."""

    async def lookup(self, ip_address: str) -> SessionLocation | None:
        return None


def build_geoip_service(settings: Settings) -> GeoIPService:
    """Instantiate the configured GeoIP service."""

    provider = (settings.geoip_provider or "none").strip().lower()
    if provider == "maxmind":
        provider = "maxmind_db"
    cache_ttl = settings.geoip_cache_ttl_seconds
    cache_capacity = settings.geoip_cache_max_entries
    timeout = settings.geoip_http_timeout_seconds

    if provider in ("", "none"):
        return NullGeoIPService()
    if provider == "ipinfo":
        if not settings.geoip_ipinfo_token:
            raise ValueError("GEOIP_IPINFO_TOKEN is required when GEOIP_PROVIDER=ipinfo.")
        return IPinfoGeoIPService(
            token=settings.geoip_ipinfo_token,
            timeout_seconds=timeout,
            cache_ttl_seconds=cache_ttl,
            cache_max_entries=cache_capacity,
        )
    if provider == "ip2location":
        if not settings.geoip_ip2location_api_key:
            raise ValueError(
                "GEOIP_IP2LOCATION_API_KEY is required when GEOIP_PROVIDER=ip2location."
            )
        return IP2LocationHTTPService(
            api_key=settings.geoip_ip2location_api_key,
            timeout_seconds=timeout,
            cache_ttl_seconds=cache_ttl,
            cache_max_entries=cache_capacity,
        )
    if provider == "maxmind_db":
        if not settings.geoip_maxmind_db_path:
            raise ValueError(
                "GEOIP_MAXMIND_DB_PATH must be set when GEOIP_PROVIDER=maxmind_db."
            )
        return MaxMindDBGeoIPService(
            db_path=settings.geoip_maxmind_db_path,
            cache_ttl_seconds=cache_ttl,
            cache_max_entries=cache_capacity,
        )
    if provider == "ip2location_db":
        if not settings.geoip_ip2location_db_path:
            raise ValueError(
                "GEOIP_IP2LOCATION_DB_PATH must be set when GEOIP_PROVIDER=ip2location_db."
            )
        return IP2LocationDatabaseService(
            db_path=settings.geoip_ip2location_db_path,
            cache_ttl_seconds=cache_ttl,
            cache_max_entries=cache_capacity,
        )
    raise ValueError(
        "Unsupported GEOIP_PROVIDER value. Expected one of "
        "none, ipinfo, ip2location, maxmind_db, ip2location_db."
    )


async def shutdown_geoip_service(service: GeoIPService | None) -> None:
    """Best-effort shutdown hook for providers that hold resources."""

    if not service:
        return
    closer = getattr(service, "aclose", None)
    if callable(closer):
        result = closer()
        if inspect.isawaitable(result):
            await result
        return
    sync_close = getattr(service, "close", None)
    if callable(sync_close):
        result = sync_close()
        if inspect.isawaitable(result):
            await result


def get_geoip_service() -> GeoIPService:
    """Return the configured GeoIP service (defaults to a no-op implementation)."""

    from app.bootstrap.container import get_container

    return get_container().geoip_service


__all__ = [
    "GeoIPService",
    "NullGeoIPService",
    "build_geoip_service",
    "get_geoip_service",
    "shutdown_geoip_service",
]
