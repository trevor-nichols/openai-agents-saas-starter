"""GeoIP provider implementations and shared helpers."""

from __future__ import annotations

import asyncio
import ipaddress
from dataclasses import dataclass
from pathlib import Path
from time import monotonic

import httpx
from geoip2 import database
from geoip2.errors import AddressNotFoundError

from app.domain.auth import SessionLocation
from app.observability.logging import log_event

_ip2location_import_error: ImportError | None
try:  # pragma: no cover - optional dependency imported lazily
    import IP2Location
except ImportError as exc:  # pragma: no cover - should be installed via pyproject
    IP2Location = None
    _ip2location_import_error = exc
else:
    _ip2location_import_error = None

_MISS = object()


def _normalize_ip(ip_address: str | None) -> str | None:
    if not ip_address:
        return None
    candidate = ip_address.strip()
    if not candidate:
        return None
    try:
        parsed = ipaddress.ip_address(candidate)
    except ValueError:
        return None
    if any(
        [
            parsed.is_private,
            parsed.is_loopback,
            parsed.is_link_local,
            parsed.is_reserved,
            parsed.is_multicast,
            parsed.is_unspecified,
        ]
    ):
        return None
    return str(parsed)


@dataclass(slots=True)
class _TTLCacheEntry:
    expires_at: float
    value: SessionLocation | None


class _TTLCache:
    def __init__(self, ttl_seconds: float, max_entries: int) -> None:
        self._ttl = max(ttl_seconds, 0.0)
        self._max_entries = max(1, max_entries)
        self._entries: dict[str, _TTLCacheEntry] = {}

    def get(self, key: str) -> SessionLocation | None | object:
        if self._ttl == 0:
            return _MISS
        entry = self._entries.get(key)
        if not entry:
            return _MISS
        if entry.expires_at <= monotonic():
            self._entries.pop(key, None)
            return _MISS
        return entry.value

    def set(self, key: str, value: SessionLocation | None) -> None:
        if self._ttl == 0:
            return
        expires_at = monotonic() + self._ttl
        self._entries[key] = _TTLCacheEntry(expires_at=expires_at, value=value)
        if len(self._entries) <= self._max_entries:
            return
        oldest_key = min(self._entries.items(), key=lambda item: item[1].expires_at)[0]
        self._entries.pop(oldest_key, None)


class BaseGeoIPService:
    """Shared helpers for GeoIP providers."""

    def __init__(self, *, cache_ttl_seconds: float, cache_max_entries: int) -> None:
        self._cache = _TTLCache(cache_ttl_seconds, cache_max_entries)

    async def _cached_lookup(self, ip_address: str) -> SessionLocation | None | object:
        return self._cache.get(ip_address)

    def _cache_result(self, ip_address: str, value: SessionLocation | None) -> None:
        self._cache.set(ip_address, value)


class IPinfoGeoIPService(BaseGeoIPService):
    """GeoIP provider backed by the IPinfo HTTP API."""

    def __init__(
        self,
        *,
        token: str,
        base_url: str = "https://ipinfo.io",
        timeout_seconds: float = 2.0,
        cache_ttl_seconds: float = 600.0,
        cache_max_entries: int = 2048,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not token:
            raise ValueError("IPinfo token is required.")
        super().__init__(
            cache_ttl_seconds=cache_ttl_seconds,
            cache_max_entries=cache_max_entries,
        )
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._client = client or httpx.AsyncClient(timeout=self._timeout)
        self._owns_client = client is None

    async def lookup(self, ip_address: str) -> SessionLocation | None:
        normalized = _normalize_ip(ip_address)
        if not normalized:
            return None
        cached = await self._cached_lookup(normalized)
        if cached is not _MISS:
            return cached  # type: ignore[return-value]
        try:
            response = await self._client.get(
                f"{self._base_url}/{normalized}",
                params={"token": self._token},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("bogon"):
                result = None
            else:
                result = SessionLocation(
                    city=(payload.get("city") or None),
                    region=(payload.get("region") or None),
                    country=(payload.get("country") or None),
                )
        except httpx.TimeoutException:
            log_event(
                "geoip.lookup_timeout",
                provider="ipinfo",
                ip=normalized,
            )
            result = None
        except httpx.HTTPStatusError as exc:
            log_event(
                "geoip.lookup_http_error",
                provider="ipinfo",
                status=exc.response.status_code,
                ip=normalized,
            )
            result = None
        except httpx.HTTPError as exc:
            log_event(
                "geoip.lookup_transport_error",
                provider="ipinfo",
                ip=normalized,
                detail=str(exc),
            )
            result = None
        except ValueError as exc:
            log_event(
                "geoip.lookup_parse_error",
                provider="ipinfo",
                ip=normalized,
                detail=str(exc),
            )
            result = None
        self._cache_result(normalized, result)
        return result

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()


class MaxMindDBGeoIPService(BaseGeoIPService):
    """GeoIP provider backed by a local MaxMind GeoIP2/GeoLite2 database."""

    def __init__(
        self,
        *,
        db_path: str | Path,
        cache_ttl_seconds: float = 900.0,
        cache_max_entries: int = 4096,
    ) -> None:
        path = Path(db_path)
        if not path.exists():
            raise FileNotFoundError(f"MaxMind database not found at {path}")
        super().__init__(
            cache_ttl_seconds=cache_ttl_seconds,
            cache_max_entries=cache_max_entries,
        )
        self._reader = database.Reader(str(path))

    async def lookup(self, ip_address: str) -> SessionLocation | None:
        normalized = _normalize_ip(ip_address)
        if not normalized:
            return None
        cached = await self._cached_lookup(normalized)
        if cached is not _MISS:
            return cached  # type: ignore[return-value]
        try:
            response = await asyncio.to_thread(self._reader.city, normalized)
        except AddressNotFoundError:
            result = None
        except ValueError as exc:
            log_event(
                "geoip.lookup_parse_error",
                provider="maxmind_db",
                ip=normalized,
                detail=str(exc),
            )
            result = None
        else:
            subdivision = response.subdivisions.most_specific
            result = SessionLocation(
                city=response.city.name,
                region=subdivision.name or subdivision.iso_code,
                country=response.country.iso_code,
            )
        self._cache_result(normalized, result)
        return result

    async def aclose(self) -> None:
        await asyncio.to_thread(self._reader.close)


class IP2LocationHTTPService(BaseGeoIPService):
    """GeoIP provider backed by the IP2Location HTTP API."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.ip2location.io",
        timeout_seconds: float = 2.0,
        cache_ttl_seconds: float = 600.0,
        cache_max_entries: int = 2048,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("IP2Location API key is required.")
        super().__init__(
            cache_ttl_seconds=cache_ttl_seconds,
            cache_max_entries=cache_max_entries,
        )
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._client = client or httpx.AsyncClient(timeout=self._timeout)
        self._owns_client = client is None

    async def lookup(self, ip_address: str) -> SessionLocation | None:
        normalized = _normalize_ip(ip_address)
        if not normalized:
            return None
        cached = await self._cached_lookup(normalized)
        if cached is not _MISS:
            return cached  # type: ignore[return-value]
        params = {
            "key": self._api_key,
            "ip": normalized,
            "format": "json",
        }
        try:
            response = await self._client.get(
                self._base_url,
                params=params,
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("response") == "INVALID ACCOUNT":
                log_event(
                    "geoip.lookup_invalid_credentials",
                    provider="ip2location_http",
                    ip=normalized,
                )
                result = None
            else:
                result = SessionLocation(
                    city=payload.get("city_name") or None,
                    region=payload.get("region_name") or None,
                    country=payload.get("country_code") or None,
                )
        except httpx.TimeoutException:
            log_event(
                "geoip.lookup_timeout",
                provider="ip2location_http",
                ip=normalized,
            )
            result = None
        except httpx.HTTPStatusError as exc:
            log_event(
                "geoip.lookup_http_error",
                provider="ip2location_http",
                status=exc.response.status_code,
                ip=normalized,
            )
            result = None
        except httpx.HTTPError as exc:
            log_event(
                "geoip.lookup_transport_error",
                provider="ip2location_http",
                ip=normalized,
                detail=str(exc),
            )
            result = None
        except ValueError as exc:
            log_event(
                "geoip.lookup_parse_error",
                provider="ip2location_http",
                ip=normalized,
                detail=str(exc),
            )
            result = None
        self._cache_result(normalized, result)
        return result

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()


class IP2LocationDatabaseService(BaseGeoIPService):
    """GeoIP provider backed by a local IP2Location BIN database."""

    def __init__(
        self,
        *,
        db_path: str | Path,
        cache_ttl_seconds: float = 900.0,
        cache_max_entries: int = 4096,
    ) -> None:
        if IP2Location is None:  # pragma: no cover - dependency guard
            raise RuntimeError("IP2Location package is not available.") from (
                _ip2location_import_error
            )
        path = Path(db_path)
        if not path.exists():
            raise FileNotFoundError(f"IP2Location database not found at {path}")
        super().__init__(
            cache_ttl_seconds=cache_ttl_seconds,
            cache_max_entries=cache_max_entries,
        )
        self._reader = IP2Location.IP2Location(str(path))

    async def lookup(self, ip_address: str) -> SessionLocation | None:
        normalized = _normalize_ip(ip_address)
        if not normalized:
            return None
        cached = await self._cached_lookup(normalized)
        if cached is not _MISS:
            return cached  # type: ignore[return-value]
        try:
            response = await asyncio.to_thread(self._reader.get_all, normalized)
        except Exception as exc:  # pragma: no cover - best effort logging
            log_event(
                "geoip.lookup_error",
                provider="ip2location_db",
                ip=normalized,
                detail=str(exc),
            )
            result = None
        else:
            result = SessionLocation(
                city=getattr(response, "city", None) or None,
                region=getattr(response, "region", None) or None,
                country=getattr(response, "country_short", None) or None,
            )
        self._cache_result(normalized, result)
        return result

    async def aclose(self) -> None:
        await asyncio.to_thread(self._reader.close)


__all__ = [
    "IPinfoGeoIPService",
    "IP2LocationDatabaseService",
    "IP2LocationHTTPService",
    "MaxMindDBGeoIPService",
]
