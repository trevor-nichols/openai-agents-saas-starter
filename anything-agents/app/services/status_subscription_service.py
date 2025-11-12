"""Service orchestration for status alert subscriptions."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import cast
from urllib.parse import urlparse
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings, get_settings
from app.domain.status import (
    StatusSubscription,
    StatusSubscriptionCreate,
    StatusSubscriptionListResult,
    StatusSubscriptionRepository,
    SubscriptionChannel,
    SubscriptionSeverity,
    SubscriptionStatus,
)
from app.infrastructure.notifications import (
    ResendEmailAdapter,
    ResendEmailError,
    ResendEmailRequest,
    get_resend_email_adapter,
)
from app.observability.logging import log_event
from app.services.rate_limit_service import RateLimitExceeded, RateLimitQuota, rate_limiter


@dataclass(slots=True)
class SubscriptionCreateResult:
    subscription: StatusSubscription
    verification_required: bool
    webhook_secret: str | None = None
    unsubscribe_token: str | None = None


PENDING_STATUS: SubscriptionStatus = "pending_verification"


class StatusSubscriptionService:
    def __init__(
        self,
        repository: StatusSubscriptionRepository,
        *,
        settings: Settings,
        email_adapter: ResendEmailAdapter | None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._email_adapter = email_adapter
        self._http_timeout = settings.status_subscription_webhook_timeout_seconds

    async def create_subscription(
        self,
        *,
        channel: str,
        target: str,
        severity_filter: str,
        metadata: Mapping[str, object] | None,
        tenant_id: UUID | None,
        created_by: str,
        ip_address: str | None,
    ) -> SubscriptionCreateResult:
        normalized_channel = self._normalize_channel(channel)
        normalized_target = self._normalize_target(normalized_channel, target)
        severity = self._normalize_severity(severity_filter)
        await self._enforce_rate_limit(normalized_channel, normalized_target, ip_address)

        target_hash = self._hash_target(normalized_channel, normalized_target)
        existing = await self._repository.find_active_by_target(
            channel=normalized_channel,
            target_hash=target_hash,
            severity_filter=severity,
            tenant_id=tenant_id,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active subscription already exists for this target.",
            )

        mask = self._mask_target(normalized_channel, normalized_target)
        now = datetime.now(UTC)
        verification_hash: str | None = None
        verification_expiry: datetime | None = None
        email_token: str | None = None
        challenge_hash: str | None = None
        challenge_token: str | None = None
        webhook_secret: str | None = None
        unsubscribe_token = self._generate_token()
        unsubscribe_hash = self._hash_token(unsubscribe_token)
        requires_verification = normalized_channel == "email"
        if normalized_channel == "email":
            email_token = self._generate_token()
            verification_hash = self._hash_token(email_token)
            verification_expiry = now + timedelta(
                minutes=self._settings.status_subscription_token_ttl_minutes
            )
        else:
            challenge_token = self._generate_token()
            challenge_hash = self._hash_token(challenge_token)
            webhook_secret = self._generate_secret()

        payload = StatusSubscriptionCreate(
            channel=normalized_channel,
            target=normalized_target,
            target_hash=target_hash,
            target_masked=mask,
            severity_filter=severity,
            metadata=dict(metadata or {}),
            tenant_id=tenant_id,
            created_by=created_by,
            verification_token_hash=verification_hash,
            verification_expires_at=verification_expiry,
            challenge_token_hash=challenge_hash,
            webhook_secret=webhook_secret,
            status="pending_verification",
            unsubscribe_token_hash=unsubscribe_hash,
            unsubscribe_token=unsubscribe_token,
        )
        subscription = await self._repository.create(payload)

        if normalized_channel == "email" and email_token:
            link = self._build_verification_link(subscription.id, email_token)
            await self._send_email_verification(
                target=normalized_target,
                link=link,
                unsubscribe_link=self._build_unsubscribe_link(subscription.id, unsubscribe_token),
                expires_at=verification_expiry,
            )
        elif normalized_channel == "webhook" and challenge_token and webhook_secret:
            await self._send_webhook_challenge(
                subscription=subscription,
                target=normalized_target,
                challenge_token=challenge_token,
                secret=webhook_secret,
            )

        return SubscriptionCreateResult(
            subscription=subscription,
            verification_required=requires_verification,
            webhook_secret=webhook_secret if normalized_channel == "webhook" else None,
            unsubscribe_token=unsubscribe_token,
        )

    async def verify_email_token(self, *, token: str) -> StatusSubscription:
        token_hash = self._hash_token(token)
        record = await self._repository.find_by_verification_hash(token_hash)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token invalid.")
        if record.status == "revoked":
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Subscription revoked.")
        if record.verification_expires_at and record.verification_expires_at < datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Token expired.")
        updated = await self._repository.mark_active(record.id)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate subscription.",
            )
        log_event(
            "status.subscriptions.email_verified",
            subscription_id=str(record.id),
            channel="email",
        )
        return updated

    async def confirm_webhook_challenge(self, *, token: str) -> StatusSubscription:
        token_hash = self._hash_token(token)
        record = await self._repository.find_by_challenge_hash(token_hash)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge invalid.")
        updated = await self._repository.mark_active(record.id)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate subscription.",
            )
        log_event(
            "status.subscriptions.webhook_verified",
            subscription_id=str(record.id),
            channel="webhook",
        )
        return updated

    async def get_subscription_by_unsubscribe_token(self, *, token: str) -> StatusSubscription:
        token_hash = self._hash_token(token)
        record = await self._repository.find_by_unsubscribe_hash(token_hash)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unsubscribe token invalid.",
            )
        return record

    async def unsubscribe_by_token(self, *, token: str) -> StatusSubscription:
        record = await self.get_subscription_by_unsubscribe_token(token=token)
        updated = await self._repository.mark_revoked(record.id, reason="user_unsubscribe")
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke subscription.",
            )
        log_event(
            "status.subscriptions.unsubscribed",
            subscription_id=str(record.id),
            channel=record.channel,
        )
        return updated

    async def list_subscriptions(
        self,
        *,
        tenant_id: UUID | None,
        status_filter: str | None,
        limit: int,
        cursor: str | None,
    ) -> StatusSubscriptionListResult:
        allowed_statuses: set[SubscriptionStatus] = {
            "pending_verification",
            "active",
            "revoked",
        }
        normalized_status: SubscriptionStatus | None = (
            status_filter if status_filter in allowed_statuses else None
        )
        return await self._repository.list_subscriptions(
            tenant_id=tenant_id,
            status=normalized_status,
            limit=limit,
            cursor=cursor,
        )

    async def revoke_subscription(
        self,
        subscription_id: UUID,
        *,
        reason: str | None = None,
    ) -> StatusSubscription:
        updated = await self._repository.mark_revoked(subscription_id, reason=reason)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found.",
            )
        return updated

    async def _enforce_rate_limit(
        self,
        channel: SubscriptionChannel,
        target: str,
        ip_address: str | None,
    ) -> None:
        limit = (
            self._settings.status_subscription_email_rate_limit_per_hour
            if channel == "email"
            else self._settings.status_subscription_ip_rate_limit_per_hour
        )
        quota = RateLimitQuota(
            name=f"status-subscribe-{channel}",
            limit=limit,
            window_seconds=3600,
            scope="ip",
        )
        key = [channel, ip_address or "unknown"]
        try:
            await rate_limiter.enforce(quota, key)
        except RateLimitExceeded as exc:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {exc.retry_after}s.",
            ) from exc

    def _normalize_channel(self, channel: str) -> SubscriptionChannel:
        normalized = (channel or "").strip().lower()
        if normalized not in {"email", "webhook"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported channel.",
            )
        return cast(SubscriptionChannel, normalized)

    def _normalize_target(self, channel: SubscriptionChannel, target: str) -> str:
        candidate = (target or "").strip()
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target is required.",
            )
        if channel == "email":
            return candidate.lower()
        return self._validate_webhook_target(candidate)

    def _normalize_severity(self, severity: str | None) -> SubscriptionSeverity:
        normalized = (severity or "major").strip().lower()
        if normalized not in {"all", "major", "maintenance"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid severity filter.",
            )
        return cast(SubscriptionSeverity, normalized)

    def _mask_target(self, channel: str, value: str) -> str:
        if channel == "email":
            if "@" not in value:
                return "***"
            username, domain = value.split("@", 1)
            masked_user = username[0] + "***" if username else "***"
            return f"{masked_user}@{domain}"
        return value[:6] + "…"

    def _hash_target(self, channel: SubscriptionChannel, target: str) -> str:
        payload = f"{channel}:{target}".encode()
        return hashlib.sha256(payload).hexdigest()

    def _validate_webhook_target(self, target: str) -> str:
        parsed = urlparse(target)
        if parsed.scheme.lower() != "https" or not parsed.netloc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook targets must be HTTPS URLs.",
            )
        host = parsed.hostname or ""
        if not host:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook target hostname is required.",
            )
        lowered = host.lower()
        if lowered in {"localhost", "127.0.0.1"} or lowered.endswith(".localhost"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook target cannot point to localhost.",
            )
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            ip = None
        if ip and (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook target must be a public HTTPS endpoint.",
            )
        return target

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def _generate_secret(self) -> str:
        return secrets.token_hex(32)

    def _hash_token(self, token: str) -> str:
        pepper = self._settings.status_subscription_token_pepper
        return hashlib.sha256((pepper + token).encode("utf-8")).hexdigest()

    def _build_verification_link(self, subscription_id: UUID, token: str) -> str:
        base = self._settings.app_public_url.rstrip("/")
        return f"{base}/status?subscription_id={subscription_id}&token={token}"

    def _build_unsubscribe_link(self, subscription_id: UUID, token: str) -> str:
        base = self._settings.app_public_url.rstrip("/")
        return f"{base}/status?subscription_id={subscription_id}&unsubscribe_token={token}"

    async def _send_email_verification(
        self,
        *,
        target: str,
        link: str,
        unsubscribe_link: str,
        expires_at: datetime | None,
    ) -> None:
        if not self._email_adapter or not self._settings.enable_resend_email_delivery:
            log_event(
                "status.subscriptions.email_notification",
                result="queued",
                target=target,
                link_preview=link[:32],
            )
            return
        request = ResendEmailRequest(
            to=[target],
            subject=f"Confirm status alerts for {self._settings.app_name}",
            text_body=(
                "Confirm your subscription to Anything Agents status updates by visiting "
                f"{link}. "
                "If you no longer wish to receive updates, unsubscribe here: "
                f"{unsubscribe_link}."
            ),
            html_body=(
                f"<p>Confirm your subscription by clicking <a href=\"{link}\">this link</a>. "
                f"This link expires at {expires_at.isoformat() if expires_at else 'soon'}.</p>"
                f"<p>If you did not request alerts, you can <a href=\"{unsubscribe_link}\">"
                f"unsubscribe here</a>.</p>"
            ),
            tags={"category": "status_subscription"},
            category="status_subscription",
        )
        try:
            await self._email_adapter.send_email(request)
        except ResendEmailError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Email delivery failed.",
            ) from exc

    async def _send_webhook_challenge(
        self,
        *,
        subscription: StatusSubscription,
        target: str,
        challenge_token: str,
        secret: str,
    ) -> None:
        payload = {
            "subscription_id": str(subscription.id),
            "challenge": challenge_token,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        headers = {
            "X-Status-Signature": signature,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._http_timeout) as client:
            response = await client.post(target, headers=headers, content=body)
            if response.status_code >= 300:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Webhook challenge delivery failed.",
                )


def build_status_subscription_service(
    *,
    repository: StatusSubscriptionRepository,
    settings: Settings | None = None,
) -> StatusSubscriptionService:
    resolved_settings = settings or get_settings()
    adapter = None
    if resolved_settings.enable_resend_email_delivery:
        adapter = get_resend_email_adapter(resolved_settings)
    return StatusSubscriptionService(
        repository,
        settings=resolved_settings,
        email_adapter=adapter,
    )
