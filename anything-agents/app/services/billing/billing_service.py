"""Service layer for billing plan and subscription management."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.billing import (
    BillingPlan,
    BillingRepository,
    SubscriptionInvoiceRecord,
    TenantSubscription,
    UsageTotal,
)
from app.services.billing.payment_gateway import (
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


@dataclass(slots=True)
class ProcessorSubscriptionSnapshot:
    tenant_id: str
    plan_code: str
    status: str
    auto_renew: bool
    starts_at: datetime | None
    current_period_start: datetime | None
    current_period_end: datetime | None
    trial_ends_at: datetime | None
    cancel_at: datetime | None
    seat_count: int | None
    billing_email: str | None
    processor_customer_id: str | None
    processor_subscription_id: str
    metadata: dict[str, str]


@dataclass(slots=True)
class ProcessorInvoiceLineSnapshot:
    feature_key: str
    quantity: int
    period_start: datetime | None
    period_end: datetime | None
    idempotency_key: str | None = None
    amount_cents: int | None = None


@dataclass(slots=True)
class ProcessorInvoiceSnapshot:
    tenant_id: str
    invoice_id: str
    status: str
    amount_due_cents: int
    currency: str
    period_start: datetime | None
    period_end: datetime | None
    hosted_invoice_url: str | None
    billing_reason: str | None
    collection_method: str | None
    description: str | None = None
    lines: list[ProcessorInvoiceLineSnapshot] = field(default_factory=list)


class BillingService:
    """Encapsulates billing operations while hiding persistence details."""

    def __init__(
        self,
        repository: BillingRepository | None = None,
        gateway: PaymentGateway | None = None,
    ) -> None:
        self._repository: BillingRepository | None = repository
        self._gateway: PaymentGateway = gateway or stripe_gateway

    def set_repository(self, repository: BillingRepository) -> None:
        self._repository = repository

    def set_gateway(self, gateway: PaymentGateway) -> None:
        self._gateway = gateway

    def _require_repository(self) -> BillingRepository:
        if self._repository is None:
            raise RuntimeError("Billing repository has not been configured.")
        return self._repository

    async def list_plans(self) -> list[BillingPlan]:
        return await self._require_repository().list_plans()

    async def get_plan(self, plan_code: str) -> BillingPlan:
        return await self._ensure_plan_exists(plan_code)

    async def get_subscription(self, tenant_id: str) -> TenantSubscription | None:
        try:
            return await self._require_repository().get_subscription(tenant_id)
        except ValueError:
            # Maintain backward compatibility with non-UUID tenant identifiers by
            # treating them as missing records rather than surfacing a 500.
            return None

    async def get_usage_totals(
        self,
        tenant_id: str,
        *,
        feature_keys: list[str] | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> list[UsageTotal]:
        repository = self._require_repository()
        try:
            return await repository.get_usage_totals(
                tenant_id,
                feature_keys=feature_keys,
                period_start=period_start,
                period_end=period_end,
            )
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc

    async def start_subscription(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        billing_email: str | None,
        auto_renew: bool,
        seat_count: int | None = None,
        trial_days: int | None = None,
    ) -> TenantSubscription:
        plan = await self._ensure_plan_exists(plan_code)
        try:
            processor_payload = await self._gateway.start_subscription(
                tenant_id=tenant_id,
                plan_code=plan_code,
                billing_email=billing_email,
                auto_renew=auto_renew,
                seat_count=seat_count,
                trial_days=trial_days,
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

        repository = self._require_repository()

        try:
            await repository.upsert_subscription(subscription)
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc
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
            subscription.cancel_at = datetime.now(UTC)

        try:
            await self._require_repository().upsert_subscription(subscription)
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc
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

        utc_now = datetime.now(UTC)
        start = _to_utc(period_start) if period_start else utc_now
        end = _to_utc(period_end) if period_end else utc_now

        repository = self._require_repository()

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
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc

    async def _ensure_plan_exists(self, plan_code: str) -> BillingPlan:
        plans = await self._require_repository().list_plans()
        for plan in plans:
            if plan.code == plan_code:
                return plan
        raise PlanNotFoundError(f"Plan '{plan_code}' not found.")

    async def _require_subscription(self, tenant_id: str) -> TenantSubscription:
        try:
            subscription = await self._require_repository().get_subscription(tenant_id)
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc
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
            updated = await self._require_repository().update_subscription(
                tenant_id,
                auto_renew=auto_renew,
                billing_email=billing_email,
                seat_count=seat_count,
            )
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc
        return updated

    async def sync_subscription_from_processor(
        self,
        snapshot: ProcessorSubscriptionSnapshot,
        *,
        processor_name: str = "stripe",
    ) -> TenantSubscription:
        starts_at = snapshot.starts_at or datetime.now(UTC)
        plan = await self._ensure_plan_exists(snapshot.plan_code)
        subscription = TenantSubscription(
            tenant_id=snapshot.tenant_id,
            plan_code=snapshot.plan_code,
            status=snapshot.status,
            auto_renew=snapshot.auto_renew,
            billing_email=snapshot.billing_email,
            starts_at=starts_at,
            current_period_start=snapshot.current_period_start,
            current_period_end=snapshot.current_period_end,
            trial_ends_at=snapshot.trial_ends_at,
            cancel_at=snapshot.cancel_at,
            seat_count=snapshot.seat_count or plan.seat_included,
            metadata=snapshot.metadata or {},
            processor=processor_name,
            processor_customer_id=snapshot.processor_customer_id,
            processor_subscription_id=snapshot.processor_subscription_id,
        )
        repository = self._require_repository()
        try:
            await repository.upsert_subscription(subscription)
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc
        return subscription

    async def ingest_invoice_snapshot(
        self,
        snapshot: ProcessorInvoiceSnapshot,
    ) -> None:
        repository = self._require_repository()
        period_start = _to_utc(snapshot.period_start or datetime.now(UTC))
        period_end = _to_utc(snapshot.period_end or period_start)
        currency = (snapshot.currency or "usd").upper()

        invoice_record = SubscriptionInvoiceRecord(
            tenant_id=snapshot.tenant_id,
            period_start=period_start,
            period_end=period_end,
            amount_cents=max(snapshot.amount_due_cents, 0),
            currency=currency,
            status=snapshot.status,
            processor_invoice_id=snapshot.invoice_id,
            hosted_invoice_url=snapshot.hosted_invoice_url,
        )

        try:
            await repository.upsert_invoice(invoice_record)
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc

        for line in snapshot.lines:
            if not line.feature_key or line.quantity in (None, 0):
                continue
            line_start = _to_utc(line.period_start) if line.period_start else period_start
            line_end = _to_utc(line.period_end) if line.period_end else period_end
            try:
                await repository.record_usage_from_processor(
                    snapshot.tenant_id,
                    feature_key=line.feature_key,
                    quantity=line.quantity,
                    period_start=line_start,
                    period_end=line_end,
                    idempotency_key=line.idempotency_key
                    or f"{snapshot.invoice_id}:{line.feature_key}",
                )
            except ValueError as exc:
                raise InvalidTenantIdentifierError(
                    "Tenant identifier is not a valid UUID."
                ) from exc


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def get_billing_service() -> BillingService:
    """Resolve the active billing service from the application container."""

    from app.bootstrap.container import get_container

    return get_container().billing_service


class _BillingServiceHandle:
    """Proxy exposing the container-backed billing service."""

    def __getattr__(self, name: str):
        return getattr(get_billing_service(), name)


billing_service = _BillingServiceHandle()
