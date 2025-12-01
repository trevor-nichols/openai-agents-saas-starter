"""Fan-out dispatcher that delivers status incidents to subscribers."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime
from uuid import UUID

import httpx

from app.core.settings import Settings, get_settings
from app.domain.status import (
    IncidentRecord,
    StatusSubscription,
    StatusSubscriptionRepository,
    SubscriptionStatus,
)
from app.infrastructure.notifications import (
    ResendEmailAdapter,
    ResendEmailError,
    ResendEmailRequest,
    get_resend_email_adapter,
)
from app.observability.logging import log_event
from app.services.integrations.slack_notifier import SlackNotificationError, SlackNotifier

ACTIVE_STATUS: SubscriptionStatus = "active"


class StatusAlertDispatcher:
    """Dispatch incidents to subscribed email/webhook channels."""

    def __init__(
        self,
        repository: StatusSubscriptionRepository,
        *,
        settings: Settings,
        email_adapter: ResendEmailAdapter | None,
        slack_notifier: SlackNotifier | None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._email_adapter = email_adapter
        self._http_timeout = settings.status_subscription_webhook_timeout_seconds
        self._slack_notifier = slack_notifier

    async def dispatch_incident(
        self,
        incident: IncidentRecord,
        *,
        severity: str = "major",
        tenant_id: UUID | None = None,
    ) -> int:
        """Send incident notifications to all matching subscriptions."""

        matched = 0
        cursor: str | None = None
        limit = 200
        severity_normalized = severity.lower()
        while True:
            result = await self._repository.list_subscriptions(
                tenant_id=tenant_id,
                status=ACTIVE_STATUS,
                limit=limit,
                cursor=cursor,
            )
            if not result.items:
                break
            for subscription in result.items:
                if not self._should_notify(subscription, severity_normalized):
                    continue
                await self._deliver(subscription, incident)
                matched += 1
            if not result.next_cursor:
                break
            cursor = result.next_cursor
        slack_dispatched = await self._notify_slack(
            incident=incident,
            severity=severity_normalized,
            tenant_id=tenant_id,
        )
        return matched + slack_dispatched

    def _should_notify(self, subscription: StatusSubscription, severity: str) -> bool:
        if subscription.status != ACTIVE_STATUS:
            return False
        if severity == "all":
            return True
        if subscription.severity_filter == "all":
            return True
        if subscription.severity_filter == "major" and severity in {"major", "incident"}:
            return True
        if subscription.severity_filter == "maintenance" and severity == "maintenance":
            return True
        return False

    async def _deliver(self, subscription: StatusSubscription, incident: IncidentRecord) -> None:
        target = await self._repository.get_delivery_target(subscription.id)
        if not target:
            log_event(
                "status.alert_dispatch.skipped",
                subscription_id=str(subscription.id),
                reason="missing_target",
            )
            return
        if subscription.channel == "email":
            await self._send_email(subscription, incident, target)
            return
        secret = await self._repository.get_webhook_secret(subscription.id)
        await self._send_webhook(subscription, incident, target, secret)

    async def _send_email(
        self,
        subscription: StatusSubscription,
        incident: IncidentRecord,
        target: str,
    ) -> None:
        unsubscribe_token = await self._ensure_unsubscribe_token(subscription.id)
        if not unsubscribe_token:
            log_event(
                "status.alert_dispatch.email_skipped",
                subscription_id=str(subscription.id),
                incident_id=incident.incident_id,
                reason="unsubscribe_token_unavailable",
            )
            return
        unsubscribe_link = self._build_unsubscribe_link(subscription.id, unsubscribe_token)
        if not self._email_adapter or not self._settings.enable_resend_email_delivery:
            log_event(
                "status.alert_dispatch.email_queued",
                subscription_id=str(subscription.id),
                incident_id=incident.incident_id,
                target=target,
                unsubscribe_link=unsubscribe_link,
            )
            return
        request = ResendEmailRequest(
            to=[target],
            subject=f"[{incident.state.title()}] {incident.service} incident",
            text_body=self._render_email_body(incident, unsubscribe_link),
            html_body=self._render_email_body(incident, unsubscribe_link, html=True),
            tags={"category": "status_subscription"},
            category="status_subscription",
        )
        try:
            await self._email_adapter.send_email(request)
            log_event(
                "status.alert_dispatch.email_sent",
                subscription_id=str(subscription.id),
                incident_id=incident.incident_id,
                unsubscribe_link=unsubscribe_link,
            )
        except ResendEmailError as exc:
            log_event(
                "status.alert_dispatch.email_error",
                subscription_id=str(subscription.id),
                incident_id=incident.incident_id,
                reason=str(exc),
            )

    async def _send_webhook(
        self,
        subscription: StatusSubscription,
        incident: IncidentRecord,
        target: str,
        secret: str | None,
    ) -> None:
        payload = {
            "subscription_id": str(subscription.id),
            "incident_id": incident.incident_id,
            "service": incident.service,
            "state": incident.state,
            "impact": incident.impact,
            "occurred_at": incident.occurred_at.isoformat(),
            "dispatched_at": datetime.now(UTC).isoformat(),
        }
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        headers = {"Content-Type": "application/json"}
        if secret:
            signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
            headers["X-Status-Signature"] = signature
        try:
            async with httpx.AsyncClient(timeout=self._http_timeout) as client:
                response = await client.post(target, headers=headers, content=body)
            if response.status_code >= 300:
                log_event(
                    "status.alert_dispatch.webhook_error",
                    subscription_id=str(subscription.id),
                    incident_id=incident.incident_id,
                    status_code=response.status_code,
                )
                return
            log_event(
                "status.alert_dispatch.webhook_sent",
                subscription_id=str(subscription.id),
                incident_id=incident.incident_id,
            )
        except httpx.HTTPError as exc:
            log_event(
                "status.alert_dispatch.webhook_exception",
                subscription_id=str(subscription.id),
                incident_id=incident.incident_id,
                reason=str(exc),
            )

    async def _notify_slack(
        self,
        *,
        incident: IncidentRecord,
        severity: str,
        tenant_id: UUID | None,
    ) -> int:
        notifier = self._slack_notifier
        if (notifier is None) or not self._settings.enable_slack_status_notifications:
            return 0
        channels = self._resolve_slack_channels(tenant_id)
        dispatched = 0
        for channel in channels:
            try:
                await notifier.send_incident_alert(
                    incident=incident,
                    severity=severity,
                    channel=channel,
                    tenant_id=tenant_id,
                )
                dispatched += 1
            except SlackNotificationError as exc:
                log_event(
                    "status.alert_dispatch.slack_error",
                    channel=channel,
                    incident_id=incident.incident_id,
                    reason=str(exc),
                )
        return dispatched

    def _resolve_slack_channels(self, tenant_id: UUID | None) -> list[str]:
        mapping = self._settings.slack_status_tenant_channel_map
        if tenant_id:
            tenant_channels = mapping.get(str(tenant_id).lower(), [])
            if tenant_channels:
                return list(tenant_channels)
        return list(self._settings.slack_status_default_channels)

    async def _ensure_unsubscribe_token(self, subscription_id: UUID) -> str | None:
        token = await self._repository.get_unsubscribe_token(subscription_id)
        if token:
            return token
        new_token = self._generate_token()
        token_hash = self._hash_token(new_token)
        updated = await self._repository.set_unsubscribe_token(
            subscription_id,
            token_hash=token_hash,
            token=new_token,
        )
        return new_token if updated else None

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def _hash_token(self, token: str) -> str:
        pepper = self._settings.status_subscription_token_pepper
        return hashlib.sha256((pepper + token).encode("utf-8")).hexdigest()

    def _build_unsubscribe_link(self, subscription_id: UUID, token: str) -> str:
        base = self._settings.app_public_url.rstrip("/")
        return f"{base}/status?subscription_id={subscription_id}&unsubscribe_token={token}"

    def _render_email_body(
        self,
        incident: IncidentRecord,
        unsubscribe_link: str,
        *,
        html: bool = False,
    ) -> str:
        lines = [
            f"Service: {incident.service}",
            f"State: {incident.state}",
            f"Impact: {incident.impact}",
            f"Occurred: {incident.occurred_at.isoformat()}",
        ]
        if not html:
            lines.extend(["", f"Manage alerts: {unsubscribe_link}"])
            return "\n".join(lines)
        escaped_link = unsubscribe_link.replace('"', "")
        details = "<br />".join(lines)
        return (
            f"{details}<br /><br />"
            f'<a href="{escaped_link}">Unsubscribe from these status updates</a>'
        )


def build_status_alert_dispatcher(
    *,
    repository: StatusSubscriptionRepository,
    settings: Settings | None = None,
    slack_notifier: SlackNotifier | None = None,
) -> StatusAlertDispatcher:
    resolved = settings or get_settings()
    adapter = None
    if resolved.enable_resend_email_delivery:
        adapter = get_resend_email_adapter(resolved)
    return StatusAlertDispatcher(
        repository,
        settings=resolved,
        email_adapter=adapter,
        slack_notifier=slack_notifier,
    )
