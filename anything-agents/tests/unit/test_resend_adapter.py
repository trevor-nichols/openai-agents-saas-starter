from __future__ import annotations

import pytest
from resend import exceptions as resend_exceptions

from app.infrastructure.notifications.resend import (
    ResendEmailAdapter,
    ResendEmailError,
    ResendEmailRequest,
)


@pytest.mark.asyncio
async def test_resend_adapter_sends_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_send(payload: dict[str, object], options: dict[str, object] | None = None):
        captured["payload"] = payload
        captured["options"] = options
        return {"id": "email_123"}

    monkeypatch.setattr(
        "app.infrastructure.notifications.resend.resend.Emails.send",
        fake_send,
    )

    adapter = ResendEmailAdapter(api_key="re_test", default_from="noreply@example.com")
    request = ResendEmailRequest(
        to="user@example.com",
        subject="Hello",
        html_body="<p>hi</p>",
        text_body="hi",
        category="email_verification",
    )
    result = await adapter.send_email(request, idempotency_key="dedupe-1")

    assert result.message_id == "email_123"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["from"] == "noreply@example.com"
    assert payload["to"] == ["user@example.com"]
    assert captured["options"] == {"idempotency_key": "dedupe-1"}


@pytest.mark.asyncio
async def test_resend_adapter_raises_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_send(payload: dict[str, object], options=None):
        raise resend_exceptions.ValidationError("bad", "validation_error", 400)

    monkeypatch.setattr(
        "app.infrastructure.notifications.resend.resend.Emails.send",
        fake_send,
    )

    adapter = ResendEmailAdapter(api_key="re_test", default_from="noreply@example.com")
    request = ResendEmailRequest(
        to="user@example.com",
        subject="Hello",
        html_body="<p>hi</p>",
        text_body="hi",
    )
    with pytest.raises(ResendEmailError):
        await adapter.send_email(request)
