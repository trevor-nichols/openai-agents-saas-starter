"""Usage metering services for billing."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.billing import UsageTotal
from app.services.billing.context import BillingContext
from app.services.billing.errors import raise_invalid_tenant, raise_payment_provider
from app.services.billing.payment_gateway import PaymentGatewayError
from app.services.billing.queries import (
    require_processor_subscription_id,
    require_subscription,
)
from app.services.billing.utils import to_utc


class BillingUsageService:
    """Tracks metered usage through the payment gateway and persistence layer."""

    def __init__(self, context: BillingContext) -> None:
        self._context = context

    async def get_usage_totals(
        self,
        tenant_id: str,
        *,
        feature_keys: list[str] | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> list[UsageTotal]:
        repository = self._context.require_repository()
        try:
            return await repository.get_usage_totals(
                tenant_id,
                feature_keys=feature_keys,
                period_start=period_start,
                period_end=period_end,
            )
        except ValueError as exc:
            raise_invalid_tenant(exc)

    async def record_usage(
        self,
        tenant_id: str,
        feature_key: str,
        quantity: int,
        idempotency_key: str | None = None,
        *,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> None:
        repository = self._context.require_repository()
        subscription = await require_subscription(repository, tenant_id)
        processor_subscription_id = require_processor_subscription_id(subscription)

        try:
            await self._context.require_gateway().record_usage(
                processor_subscription_id,
                feature_key=feature_key,
                quantity=quantity,
                idempotency_key=idempotency_key,
                period_start=period_start,
                period_end=period_end,
            )
        except PaymentGatewayError as exc:
            raise_payment_provider(exc)

        utc_now = datetime.now(UTC)
        start = to_utc(period_start) if period_start else utc_now
        end = to_utc(period_end) if period_end else utc_now

        try:
            await repository.record_usage(
                tenant_id,
                feature_key=feature_key,
                quantity=quantity,
                period_start=start,
                period_end=end,
                idempotency_key=idempotency_key,
            )
        except ValueError as exc:
            raise_invalid_tenant(exc)


__all__ = ["BillingUsageService"]
