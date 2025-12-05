from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

from app.core.settings import Settings
from app.infrastructure.geoip.providers import IPinfoGeoIPService
from app.services.geoip_service import (
    NullGeoIPService,
    build_geoip_service,
    shutdown_geoip_service,
)


def _settings(**overrides: object) -> Settings:
    defaults: dict[str, object] = {
        "geoip_provider": "none",
        "geoip_ipinfo_token": None,
        "geoip_ip2location_api_key": None,
        "geoip_maxmind_db_path": None,
        "geoip_ip2location_db_path": None,
        "geoip_cache_ttl_seconds": 60.0,
        "geoip_cache_max_entries": 128,
        "geoip_http_timeout_seconds": 1.0,
    }
    overrides_dict: dict[str, object] = dict(overrides)
    defaults.update(overrides_dict)
    return cast(Settings, SimpleNamespace(**defaults))


def test_build_geoip_service_defaults_to_null() -> None:
    service = build_geoip_service(_settings())
    assert isinstance(service, NullGeoIPService)


def test_build_geoip_service_requires_token_for_ipinfo() -> None:
    with pytest.raises(ValueError):
        build_geoip_service(_settings(geoip_provider="ipinfo"))


@pytest.mark.asyncio
async def test_build_geoip_service_constructs_ipinfo() -> None:
    settings = _settings(geoip_provider="ipinfo", geoip_ipinfo_token="token")
    service = build_geoip_service(settings)
    assert isinstance(service, IPinfoGeoIPService)
    await shutdown_geoip_service(service)
