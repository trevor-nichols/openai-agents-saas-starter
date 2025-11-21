from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from app.domain.auth import SessionLocation
from app.infrastructure.geoip import providers
from app.infrastructure.geoip.providers import (
    IP2LocationDatabaseService,
    IP2LocationHTTPService,
    IPinfoGeoIPService,
    MaxMindDBGeoIPService,
)


@pytest.mark.asyncio
async def test_ipinfo_lookup_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.path.endswith("/8.8.8.8")
        return httpx.Response(
            200,
            json={"city": "Mountain View", "region": "California", "country": "US"},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = IPinfoGeoIPService(token="token", client=client, cache_ttl_seconds=30)
    try:
        first = await service.lookup("8.8.8.8")
        second = await service.lookup("8.8.8.8")
    finally:
        await service.aclose()
    assert first == SessionLocation(city="Mountain View", region="California", country="US")
    assert second == first
    assert calls == 1


@pytest.mark.asyncio
async def test_ip2location_http_invalid_account(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "INVALID ACCOUNT"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = IP2LocationHTTPService(api_key="abc", client=client, cache_ttl_seconds=10)
    try:
        result = await service.lookup("1.1.1.1")
    finally:
        await service.aclose()
    assert result is None


@pytest.mark.asyncio
async def test_maxmind_db_lookup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "GeoLite2-City.mmdb"
    db_path.write_bytes(b"stub")

    class DummyReader:
        def __init__(self, path: str) -> None:
            self.path = path
            self.closed = False

        def city(self, ip: str) -> SimpleNamespace:
            assert ip == "8.8.4.4"
            return SimpleNamespace(
                city=SimpleNamespace(name="London"),
                subdivisions=SimpleNamespace(
                    most_specific=SimpleNamespace(name="England", iso_code="ENG")
                ),
                country=SimpleNamespace(iso_code="GB"),
            )

        def close(self) -> None:
            self.closed = True

    reader = DummyReader(str(db_path))
    monkeypatch.setattr(providers.database, "Reader", lambda _: reader)
    service = MaxMindDBGeoIPService(db_path=str(db_path), cache_ttl_seconds=0)
    result = await service.lookup("8.8.4.4")
    assert result == SessionLocation(city="London", region="England", country="GB")
    await service.aclose()
    assert reader.closed is True


@pytest.mark.asyncio
async def test_ip2location_db_lookup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "IP2LOCATION-LITE-DB3.BIN"
    db_path.write_bytes(b"stub")

    class DummyIP2LocationReader:
        def __init__(self, path: str) -> None:
            self.path = path
            self.closed = False

        def get_all(self, ip: str) -> SimpleNamespace:
            assert ip == "4.4.4.4"
            return SimpleNamespace(city="Paris", region="Ile-de-France", country_short="FR")

        def close(self) -> None:
            self.closed = True

    dummy_reader = DummyIP2LocationReader(str(db_path))
    monkeypatch.setattr(
        providers,
        "IP2Location",
        SimpleNamespace(IP2Location=lambda _: dummy_reader),
    )
    monkeypatch.setattr(providers, "_ip2location_import_error", None)
    service = IP2LocationDatabaseService(db_path=str(db_path), cache_ttl_seconds=0)
    result = await service.lookup("4.4.4.4")
    assert result == SessionLocation(city="Paris", region="Ile-de-France", country="FR")
    await service.aclose()
    assert dummy_reader.closed is True
