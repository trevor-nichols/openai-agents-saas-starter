"""Pluggable GeoIP lookup stub used by the auth session pipeline."""

from __future__ import annotations

from typing import Protocol

from app.domain.auth import SessionLocation


class GeoIPService(Protocol):
    """Async interface for translating IP addresses into coarse locations."""

    async def lookup(self, ip_address: str) -> SessionLocation | None: ...


class NullGeoIPService:
    """Default GeoIP implementation that always returns None."""

    async def lookup(self, ip_address: str) -> SessionLocation | None:
        return None


_GEOIP_SINGLETON: GeoIPService | None = None


def get_geoip_service() -> GeoIPService:
    """Return the configured GeoIP service (defaults to a no-op implementation)."""

    global _GEOIP_SINGLETON
    if _GEOIP_SINGLETON is None:
        _GEOIP_SINGLETON = NullGeoIPService()
    return _GEOIP_SINGLETON
