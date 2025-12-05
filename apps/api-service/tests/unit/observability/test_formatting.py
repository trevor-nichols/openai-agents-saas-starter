from __future__ import annotations

import json
import logging

from app.observability.logging.formatting import JSONLogFormatter, StructuredLoggingConfig


def test_formatter_injects_service_env_and_context() -> None:
    formatter = JSONLogFormatter(
        config=StructuredLoggingConfig(service="svc", environment="prod"),
        context_provider=lambda: {"tenant_id": "tenant-123"},
    )

    record = logging.LogRecord("unit.logger", logging.INFO, "", 0, "hello", (), None)
    record.structured = {"event": "unit.event", "fields": {"foo": "bar"}}

    payload = json.loads(formatter.format(record))

    assert payload["service"] == "svc"
    assert payload["environment"] == "prod"
    assert payload["tenant_id"] == "tenant-123"
    assert payload["fields"]["foo"] == "bar"
    assert payload["event"] == "unit.event"

