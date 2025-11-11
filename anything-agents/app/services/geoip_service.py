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


def get_geoip_service() -> GeoIPService:
    """Return the configured GeoIP service (defaults to a no-op implementation)."""

    from app.bootstrap.container import get_container

    return get_container().geoip_service
