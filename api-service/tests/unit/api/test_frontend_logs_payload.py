from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.v1.logs.router import FrontendLogPayload, MAX_FIELDS


def test_frontend_log_payload_rejects_extra_fields() -> None:
    fields = {f"key{i}": i for i in range(MAX_FIELDS + 1)}
    with pytest.raises(ValidationError):
        FrontendLogPayload(event="ui.click", fields=fields)


def test_frontend_log_payload_accepts_basic_event() -> None:
    payload = FrontendLogPayload(event="ui.click", message="clicked")
    assert payload.event == "ui.click"
    assert payload.level == "info"
