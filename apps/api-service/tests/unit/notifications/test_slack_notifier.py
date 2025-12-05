from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import httpx
import pytest

from app.core.settings import get_settings
from app.domain.status import (
    IncidentRecord,
    StatusSubscriptionListResult,
    StatusSubscriptionRepository,
)
from app.services.integrations.slack_notifier import SlackNotifier
from app.services.status.status_alert_dispatcher import StatusAlertDispatcher


def _incident() -> IncidentRecord:
    return IncidentRecord(
        incident_id="inc_123",
        service="Conversations",
        occurred_at=datetime.now(UTC),
        impact="Intermittent latency",
        state="investigating",
    )


@pytest.mark.asyncio
async def test_slack_notifier_sends_message() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        payload = json.loads(request.content)
        assert payload["channel"] == "C123"
        return httpx.Response(200, json={"ok": True, "ts": "1"})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://slack.com/api")
    notifier = SlackNotifier(
        token="xoxb-test",
        base_url="https://slack.com/api",
        timeout_seconds=2,
        rate_limit_window_seconds=0.0,
        max_retries=1,
        client=client,
    )
    await notifier.send_incident_alert(
        incident=_incident(),
        severity="major",
        channel="C123",
        tenant_id=None,
    )
    await notifier.shutdown()
    await client.aclose()
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_slack_notifier_retries_on_rate_limit() -> None:
    responses = [
        httpx.Response(429, headers={"Retry-After": "0.01"}, json={"ok": False}),
        httpx.Response(200, json={"ok": True}),
    ]

    def handler(_: httpx.Request) -> httpx.Response:
        return responses.pop(0)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://slack.com/api")
    notifier = SlackNotifier(
        token="xoxb-test",
        base_url="https://slack.com/api",
        timeout_seconds=2,
        rate_limit_window_seconds=0.0,
        max_retries=2,
        client=client,
    )
    await notifier.send_incident_alert(
        incident=_incident(),
        severity="major",
        channel="C999",
        tenant_id=None,
    )
    await notifier.shutdown()
    await client.aclose()
    assert not responses


class _EmptyStatusRepository:
    async def list_subscriptions(self, **_: object) -> StatusSubscriptionListResult:
        return StatusSubscriptionListResult(items=[], next_cursor=None)


class _StubSlackNotifier:
    def __init__(self) -> None:
        self.channels: list[str] = []

    async def send_incident_alert(self, **kwargs: object) -> None:
        channel = str(kwargs.get("channel"))
        self.channels.append(channel)


@pytest.mark.asyncio
async def test_dispatcher_counts_slack_channels() -> None:
    tenant_id = UUID("12345678-1234-5678-1234-567812345678")
    base_settings = get_settings()
    settings = base_settings.model_copy(
        update={
            "enable_slack_status_notifications": True,
            "slack_status_default_channels": ["CDEFAULT"],
            "slack_status_tenant_channel_map": {str(tenant_id): ["CTENANT"]},
        }
    )
    notifier = _StubSlackNotifier()
    repository = cast(StatusSubscriptionRepository, _EmptyStatusRepository())
    slack = cast(SlackNotifier, notifier)
    dispatcher = StatusAlertDispatcher(
        repository,
        settings=settings,
        email_adapter=None,
        slack_notifier=slack,
    )
    dispatched = await dispatcher.dispatch_incident(
        _incident(),
        severity="major",
        tenant_id=tenant_id,
    )
    assert dispatched == 1
    assert notifier.channels == ["CTENANT"]
