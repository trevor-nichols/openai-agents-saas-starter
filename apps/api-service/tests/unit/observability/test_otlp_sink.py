from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from app.observability.logging.sinks.otlp import _to_otlp_payload, parse_headers


def test_parse_headers_accepts_json_object() -> None:
    headers = parse_headers('{"Authorization": "Bearer 123", "X-Tenant": "acme"}')
    assert headers == {"Authorization": "Bearer 123", "X-Tenant": "acme"}


def test_parse_headers_rejects_invalid_json() -> None:
    with pytest.raises(ValueError):
        parse_headers("not-json")

    with pytest.raises(ValueError):
        parse_headers('["array-not-object"]')


def test_otlp_payload_includes_attributes_and_timestamp() -> None:
    ts_str = "2025-01-01T00:00:00Z"
    entry = {
        "ts": ts_str,
        "level": "info",
        "logger": "unit.logger",
        "service": "svc",
        "environment": "prod",
        "message": "hello",
        "extra": "value",
    }

    payload = _to_otlp_payload(entry)
    record = payload["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]

    expected_ns = int(
        datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(
            tzinfo=timezone.utc
        ).timestamp()
        * 1_000_000_000
    )

    assert record["body"]["stringValue"] == "hello"
    assert record["severityText"] == "INFO"
    assert record["timeUnixNano"] == str(expected_ns)

    attrs = {item["key"]: item["value"] for item in record["attributes"]}
    assert "extra" in attrs
    assert attrs["extra"]["stringValue"] == "value"

    # Ensure resource attributes carry service/env.
    resource_attrs = {item["key"]: item["value"] for item in payload["resourceLogs"][0]["resource"]["attributes"]}
    assert resource_attrs["service.name"]["stringValue"] == "svc"
    assert resource_attrs["deployment.environment"]["stringValue"] == "prod"

