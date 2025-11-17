"""Unit tests for structured logging helpers."""

from __future__ import annotations

import json
import logging

import pytest

from app.core.config import Settings
from app.observability.logging import (
    JSONLogFormatter,
    clear_log_context,
    configure_logging,
    get_log_context,
    log_context,
    log_event,
)


class _BufferHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - trivial transport
        self.items.append(self.format(record))


def test_log_context_scoping_restores_previous_values() -> None:
    clear_log_context()
    assert get_log_context() == {}

    with log_context(correlation_id="outer"):
        assert get_log_context()["correlation_id"] == "outer"
        with log_context(correlation_id="inner"):
            assert get_log_context()["correlation_id"] == "inner"
        assert get_log_context()["correlation_id"] == "outer"

    assert get_log_context() == {}


def test_log_event_emits_context_and_fields() -> None:
    clear_log_context()
    handler = _BufferHandler()
    handler.setFormatter(JSONLogFormatter())

    logger = logging.getLogger("anything-agents.observability")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    try:
        with log_context(correlation_id="ctx-123"):
            log_event(
                "unit.test",
                tenant_id="tenant-42",
                quota="signup.per_hour",
            )
    finally:
        logger.removeHandler(handler)

    assert handler.items, "No log records captured"
    payload = json.loads(handler.items[0])
    assert payload["event"] == "unit.test"
    assert payload["correlation_id"] == "ctx-123"
    assert payload["tenant_id"] == "tenant-42"
    assert payload["fields"]["quota"] == "signup.per_hour"


def test_configure_logging_requires_datadog_api_key() -> None:
    settings = Settings.model_validate({"LOGGING_SINK": "datadog"})
    with pytest.raises(ValueError):
        configure_logging(settings)
