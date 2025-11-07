"""Service layer for billing plan and subscription management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.domain.billing import BillingPlan, BillingRepository, TenantSubscription
from app.infrastructure.persistence.billing.in_memory import InMemoryBillingRepository
from app.services.payment_gateway import (
    PaymentGateway,
    PaymentGatewayError,
    stripe_gateway,
)


class BillingError(Exception):
    """Base class for billing-related failures."""


class PlanNotFoundError(BillingError):
    """Raised when the requested plan does not exist."""


class SubscriptionNotFoundError(BillingError):
    """Raised when no subscription exists for the tenant."""


class SubscriptionStateError(BillingError):
    """Raised when subscription state prevents the requested operation."""


class InvalidTenantIdentifierError(BillingError):
    """Raised when the provided tenant identifier is not valid for persistence."""


class PaymentProviderError(BillingError):
    """Raised when the payment gateway rejects a request."""


class BillingService:
    """Encapsulates billing operations while hiding persistence details."""

    def __init__(
        self,
        repository: Optional[BillingRepository] = None,
        gateway: PaymentGateway | None = None,
    ) -> None:
        self._repository: BillingRepository = repository or InMemoryBillingRepository()
        self._gateway: PaymentGateway = gateway or stripe_gateway

    def set_repository(self, repository: BillingRepository) -> None:
        self._repository = repository

    def set_gateway(self, gateway: PaymentGateway) -> None:
        self._gateway = gateway

    async def list_plans(self) -> list[BillingPlan]:
        return await self._repository.list_plans()

    async def get_subscription(self, tenant_id: str) -> TenantSubscription | None:
        try:
            return await self._repository.get_subscription(tenant_id)
        except ValueError:
            # Maintain backward compatibility with non-UUID tenant identifiers by
            # treating them as missing records rather than surfacing a 500.
            return None

    async def start_subscription(
        self,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None = None,
    ) -> TenantSubscription:
        plan = await self._ensure_plan_exists(plan_code)
        try:
            processor_payload = await self._gateway.start_subscription(
                tenant_id=tenant_id,
                plan_code=plan_code,
                billing_email=billing_email,
                auto_renew=auto_renew,
                seat_count=seat_count,
            )
        except PaymentGatewayError as exc:
            raise PaymentProviderError(str(exc)) from exc

        subscription = TenantSubscription(
            tenant_id=tenant_id,
            plan_code=plan_code,
            status="active",
            auto_renew=auto_renew,
            billing_email=billing_email,
            starts_at=processor_payload.starts_at,
            current_period_start=processor_payload.current_period_start,
            current_period_end=processor_payload.current_period_end,
            trial_ends_at=processor_payload.trial_ends_at,
            seat_count=seat_count or plan.seat_included,
            metadata=processor_payload.metadata or {},
            processor=processor_payload.processor,
            processor_customer_id=processor_payload.customer_id,
            processor_subscription_id=processor_payload.subscription_id,
        )

        try:
            await self._repository.upsert_subscription(subscription)
        except ValueError as exc:
            raise InvalidTenantIdentifierError(
                "Tenant identifier is not a valid UUID."
            ) from exc
        return subscription

    async def cancel_subscription(
        self,
        tenant_id: str,
        cancel_at_period_end: bool = True,
    ) -> TenantSubscription:
        subscription = await self._require_subscription(tenant_id)

        if not subscription.processor_subscription_id:
            raise SubscriptionStateError("Subscription is missing processor identifier.")

        try:
            await self._gateway.cancel_subscription(
                subscription.processor_subscription_id,
                cancel_at_period_end=cancel_at_period_end,
            )
        except PaymentGatewayError as exc:
            raise PaymentProviderError(str(exc)) from exc

        if cancel_at_period_end:
            subscription.cancel_at = subscription.current_period_end
        else:
            subscription.status = "canceled"
            subscription.cancel_at = datetime.now(timezone.utc)

        try:
            await self._repository.upsert_subscription(subscription)
        except ValueError as exc:
            raise InvalidTenantIdentifierError(
                "Tenant identifier is not a valid UUID."
            ) from exc
        return subscription

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
        subscription = await self._require_subscription(tenant_id)

        if not subscription.processor_subscription_id:
            raise SubscriptionStateError("Subscription is missing processor identifier.")

        try:
            await self._gateway.record_usage(
                subscription.processor_subscription_id,
                feature_key=feature_key,
                quantity=quantity,
                idempotency_key=idempotency_key,
                period_start=period_start,
                period_end=period_end,
            )
        except PaymentGatewayError as exc:
            raise PaymentProviderError(str(exc)) from exc

        utc_now = datetime.now(timezone.utc)
        start = _to_utc(period_start) if period_start else utc_now
        end = _to_utc(period_end) if period_end else utc_now

        try:
            await self._repository.record_usage(
                tenant_id,
                feature_key=feature_key,
                quantity=quantity,
                period_start=start,
                period_end=end,
                idempotency_key=idempotency_key,
            )
        except ValueError as exc:
            raise InvalidTenantIdentifierError(
                "Tenant identifier is not a valid UUID."
            ) from exc

    async def _ensure_plan_exists(self, plan_code: str) -> BillingPlan:
        plans = await self._repository.list_plans()
        for plan in plans:
            if plan.code == plan_code:
                return plan
        raise PlanNotFoundError(f"Plan '{plan_code}' not found.")

    async def _require_subscription(self, tenant_id: str) -> TenantSubscription:
        try:
            subscription = await self._repository.get_subscription(tenant_id)
        except ValueError as exc:
            raise InvalidTenantIdentifierError(
                "Tenant identifier is not a valid UUID."
            ) from exc
        if subscription is None:
            raise SubscriptionNotFoundError(
                f"Tenant '{tenant_id}' does not have an active subscription."
            )
        return subscription

    async def update_subscription(
        self,
        tenant_id: str,
        *,
        auto_renew: bool | None = None,
        billing_email: str | None = None,
        seat_count: int | None = None,
    ) -> TenantSubscription:
        subscription = await self._require_subscription(tenant_id)

        if subscription.processor_subscription_id:
            try:
                await self._gateway.update_subscription(
                    subscription.processor_subscription_id,
                    auto_renew=auto_renew,
                    seat_count=seat_count,
                    billing_email=billing_email,
                )
            except PaymentGatewayError as exc:
                raise PaymentProviderError(str(exc)) from exc

        try:
            updated = await self._repository.update_subscription(
                tenant_id,
                auto_renew=auto_renew,
                billing_email=billing_email,
                seat_count=seat_count,
            )
        except ValueError as exc:
            raise InvalidTenantIdentifierError(
                "Tenant identifier is not a valid UUID."
            ) from exc
        return updated


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


billing_service = BillingService()
