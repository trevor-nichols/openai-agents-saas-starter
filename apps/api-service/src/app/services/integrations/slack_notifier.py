"""Slack adapter for incident notifications."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Final
from uuid import UUID

import httpx

from app.core.settings import Settings
from app.domain.status import IncidentRecord
from app.observability.logging import log_event
from app.observability.metrics import observe_slack_notification

logger = logging.getLogger(__name__)
_RETRYABLE_ERRORS: Final[set[str]] = {"ratelimited", "internal_error", "request_timeout"}


class SlackNotificationError(RuntimeError):
    """Raised when Slack delivery cannot be completed."""


class SlackNotifier:
    """Lightweight Slack Web API client with per-channel throttling."""

    def __init__(
        self,
        *,
        token: str,
        base_url: str,
        timeout_seconds: float,
        rate_limit_window_seconds: float,
        max_retries: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._token = token.strip()
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
        )
        self._owns_client = client is None
        self._rate_window = max(rate_limit_window_seconds, 0.1)
        self._max_retries = max(1, max_retries)
        self._channel_locks: dict[str, asyncio.Lock] = {}
        self._channel_next_ready: dict[str, float] = {}

    async def shutdown(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def send_incident_alert(
        self,
        *,
        incident: IncidentRecord,
        severity: str,
        channel: str,
        tenant_id: UUID | None,
    ) -> None:
        """Deliver a formatted incident update to Slack."""

        payload = self._build_payload(incident=incident, severity=severity, channel=channel)
        start = time.perf_counter()
        result = "error"
        try:
            await self._post_with_retries(channel, payload)
        except SlackNotificationError as exc:
            log_event(
                "status.alert_dispatch.slack_failed",
                channel=channel,
                incident_id=incident.incident_id,
                tenant_id=str(tenant_id) if tenant_id else None,
                reason=str(exc),
            )
            raise
        else:
            result = "sent"
            log_event(
                "status.alert_dispatch.slack_sent",
                channel=channel,
                incident_id=incident.incident_id,
                tenant_id=str(tenant_id) if tenant_id else None,
            )
        finally:
            duration = max(time.perf_counter() - start, 0.0)
            observe_slack_notification(channel=channel, result=result, duration_seconds=duration)

    async def _post_with_retries(self, channel: str, payload: dict[str, Any]) -> None:
        error_detail = ""
        backoff = 1.0
        for attempt in range(1, self._max_retries + 1):
            await self._respect_local_rate_limit(channel)
            try:
                response = await self._client.post(
                    "/chat.postMessage",
                    headers=self._headers,
                    json=payload,
                )
            except httpx.HTTPError as exc:
                error_detail = str(exc)
            else:
                if response.status_code == 429:
                    retry_after = self._parse_retry_after(response)
                    error_detail = f"rate_limited ({retry_after:.1f}s)"
                    await asyncio.sleep(retry_after)
                    continue
                if response.status_code >= 500:
                    error_detail = f"{response.status_code}: {response.text[:120]}"
                else:
                    success, error_detail = self._interpret_response(response)
                    if success:
                        return
                    if error_detail not in _RETRYABLE_ERRORS:
                        raise SlackNotificationError(error_detail)
            if attempt < self._max_retries:
                await asyncio.sleep(min(backoff, 5.0))
                backoff *= 2
        raise SlackNotificationError(error_detail or "Slack delivery failed")

    async def _respect_local_rate_limit(self, channel: str) -> None:
        lock = self._channel_locks.setdefault(channel, asyncio.Lock())
        async with lock:
            now = time.monotonic()
            ready_at = self._channel_next_ready.get(channel, 0.0)
            if now < ready_at:
                await asyncio.sleep(ready_at - now)
                now = time.monotonic()
            self._channel_next_ready[channel] = now + self._rate_window

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _build_payload(
        self,
        *,
        incident: IncidentRecord,
        severity: str,
        channel: str,
    ) -> dict[str, Any]:
        title = f"[{incident.state.title()}] {incident.service}"
        text = (
            f"*Impact:* {incident.impact}\n"
            f"*Severity Filter:* {severity.title()}\n"
            f"*Occurred:* {incident.occurred_at.isoformat()}"
        )
        return {
            "channel": channel,
            "text": f"{title} — {incident.impact}",
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{title}*"},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": text},
                },
            ],
        }

    @staticmethod
    def _parse_retry_after(response: httpx.Response) -> float:
        header = response.headers.get("Retry-After")
        if not header:
            return 1.0
        try:
            return max(float(header), 0.5)
        except ValueError:
            return 1.0

    @staticmethod
    def _interpret_response(response: httpx.Response) -> tuple[bool, str]:
        try:
            payload = response.json()
        except ValueError:  # pragma: no cover - Slack should always return JSON
            return False, f"{response.status_code}:malformed_body"
        if payload.get("ok"):
            return True, ""
        return False, str(payload.get("error") or "unknown_error")


def build_slack_notifier(settings: Settings) -> SlackNotifier | None:
    if not settings.enable_slack_status_notifications:
        return None
    token = settings.slack_status_bot_token
    if not token:
        return None
    return SlackNotifier(
        token=token,
        base_url=settings.slack_api_base_url,
        timeout_seconds=settings.slack_http_timeout_seconds,
        rate_limit_window_seconds=settings.slack_status_rate_limit_window_seconds,
        max_retries=settings.slack_status_max_retries,
    )


__all__ = ["SlackNotifier", "SlackNotificationError", "build_slack_notifier"]

