from __future__ import annotations

import httpx
import pytest
from starter_cli.core import CLIError
from starter_cli.workflows.setup.validators import (
    normalize_geoip_provider,
    normalize_logging_sink,
    parse_positive_int,
    probe_vault_transit,
    validate_plan_map,
    validate_redis_url,
)


def test_validate_plan_map_accepts_json() -> None:
    data = validate_plan_map('{"starter":"price_A","enterprise":"price_B"}')
    assert data["starter"] == "price_A"
    assert data["enterprise"] == "price_B"


def test_validate_plan_map_accepts_csv() -> None:
    data = validate_plan_map("solo=price_1,pro=price_2")
    assert data == {"solo": "price_1", "pro": "price_2"}


def test_validate_plan_map_rejects_invalid_entry() -> None:
    with pytest.raises(CLIError):
        validate_plan_map("invalidentry")


def test_validate_redis_url_requires_tls() -> None:
    with pytest.raises(CLIError):
        validate_redis_url("redis://cache.internal:6379/0", require_tls=True, role="Primary")


def test_validate_redis_url_requires_auth_for_managed() -> None:
    with pytest.raises(CLIError):
        validate_redis_url("rediss://cache.example.com:6380/0", require_tls=True, role="Primary")


def test_logging_sink_normalization() -> None:
    assert normalize_logging_sink("Datadog") == "datadog"
    assert normalize_logging_sink("file") == "file"
    with pytest.raises(CLIError):
        normalize_logging_sink("syslog")


def test_geoip_provider_normalization() -> None:
    assert normalize_geoip_provider("MAXMIND") == "maxmind_db"
    assert normalize_geoip_provider("ipinfo") == "ipinfo"
    assert normalize_geoip_provider("ip2location-db") == "ip2location_db"
    with pytest.raises(CLIError):
        normalize_geoip_provider("custom")


def test_parse_positive_int_enforces_minimum() -> None:
    assert parse_positive_int("10", field="rate", minimum=5) == 10
    with pytest.raises(CLIError):
        parse_positive_int("3", field="rate", minimum=5)


def test_probe_vault_transit_handles_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STARTER_CLI_SKIP_VAULT_PROBE", "false")
    def fake_request(url: str, headers: dict[str, str]):
        assert url == "https://vault.example/v1/transit/keys/auth-service"
        assert headers["X-Vault-Token"] == "token"
        return httpx.Response(403, text="denied")

    with pytest.raises(CLIError):
        probe_vault_transit(
            base_url="https://vault.example",
            token="token",
            key_name="auth-service",
            request=fake_request,
        )


def test_probe_vault_transit_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STARTER_CLI_SKIP_VAULT_PROBE", "false")
    def ok_request(url: str, headers: dict[str, str]):
        return httpx.Response(200, text="ok")

    assert probe_vault_transit(
        base_url="https://vault.example",
        token="token",
        key_name="auth-service",
        request=ok_request,
    )
