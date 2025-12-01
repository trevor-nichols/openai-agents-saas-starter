from __future__ import annotations

from typing import cast

import pytest

from app.core.settings import Settings
from app.infrastructure.notifications import ResendEmailAdapter
from app.infrastructure.notifications.resend import ResendEmailSendResult
from app.services.contact_service import (
    ContactDeliveryError,
    ContactService,
    ContactSubmissionResult,
)


class StubResendAdapter:
    def __init__(self) -> None:
        self.sent_request = None

    async def send_email(self, request):
        self.sent_request = request
        return ResendEmailSendResult(message_id="msg-123")


@pytest.mark.anyio()
async def test_contact_service_delivers_via_resend() -> None:
    settings = Settings(
        enable_resend_email_delivery=True,
        contact_email_recipients=["support@example.com"],
        contact_email_subject_prefix="[Contact]",
    )
    adapter = StubResendAdapter()
    service = ContactService(settings=settings, email_adapter=cast(ResendEmailAdapter, adapter))

    result = await service.submit_contact(
        name="Ada Lovelace",
        email="ada@example.com",
        company="Analytical Engines",
        topic="Partnership",
        message="We would like to collaborate on agent deployments.",
        ip_address="203.0.113.1",
        user_agent="pytest",
    )

    assert isinstance(result, ContactSubmissionResult)
    assert result.delivered is True
    assert result.message_id == "msg-123"
    assert adapter.sent_request is not None
    assert adapter.sent_request.to == ["support@example.com"]
    assert adapter.sent_request.reply_to == ["ada@example.com"]
    assert "Partnership" in adapter.sent_request.subject
    assert adapter.sent_request.tags == {"category": "contact", "topic": "Partnership"}


@pytest.mark.anyio()
async def test_contact_service_honors_honeypot() -> None:
    settings = Settings(
        enable_resend_email_delivery=True,
        contact_email_recipients=["support@example.com"],
    )
    adapter = StubResendAdapter()
    service = ContactService(settings=settings, email_adapter=cast(ResendEmailAdapter, adapter))

    result = await service.submit_contact(
        name="Eve",
        email="eve@example.com",
        company=None,
        topic=None,
        message="Spam attempt",
        ip_address=None,
        user_agent=None,
        honeypot="filled",
    )

    assert result.suppressed is True
    assert result.delivered is False
    assert adapter.sent_request is None


@pytest.mark.anyio()
async def test_contact_service_bypasses_delivery_when_disabled() -> None:
    settings = Settings(
        enable_resend_email_delivery=False,
        contact_email_recipients=["support@example.com"],
    )
    adapter = StubResendAdapter()
    service = ContactService(settings=settings, email_adapter=cast(ResendEmailAdapter, adapter))

    result = await service.submit_contact(
        name=None,
        email="user@example.com",
        company=None,
        topic=None,
        message="Hello world",
        ip_address=None,
        user_agent=None,
    )

    assert result.delivered is False
    assert adapter.sent_request is None
