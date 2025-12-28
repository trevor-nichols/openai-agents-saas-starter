"""Service layer for billing plan and subscription management."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from app.core.settings import get_settings
from app.domain.billing import (
    BillingCustomerRecord,
    BillingPlan,
    BillingRepository,
    SubscriptionInvoiceRecord,
    TenantSubscription,
    UsageTotal,
)
from app.services.billing.payment_gateway import (
    PaymentGateway,
    PaymentGatewayError,
    PaymentMethodSummary,
    PortalSessionResult,
    SetupIntentResult,
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


class BillingCustomerNotFoundError(BillingError):
    """Raised when no billing customer exists for the tenant."""


class InvalidTenantIdentifierError(BillingError):
    """Raised when the provided tenant identifier is not valid for persistence."""


class PaymentProviderError(BillingError):
    """Raised when the payment gateway rejects a request."""


class PlanChangeTiming(StrEnum):
    AUTO = "auto"
    IMMEDIATE = "immediate"
    PERIOD_END = "period_end"


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
    processor_schedule_id: str | None
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


@dataclass(slots=True)
class PlanChangeResult:
    subscription: TenantSubscription
    target_plan_code: str
    effective_at: datetime | None
    seat_count: int | None
    timing: PlanChangeTiming


@dataclass(slots=True)
class UpcomingInvoicePreview:
    plan_code: str
    plan_name: str
    seat_count: int | None
    invoice_id: str | None
    amount_due_cents: int
    currency: str
    period_start: datetime | None
    period_end: datetime | None
    lines: list[UpcomingInvoiceLineSnapshot] = field(default_factory=list)


@dataclass(slots=True)
class UpcomingInvoiceLineSnapshot:
    description: str | None
    amount_cents: int
    currency: str | None
    quantity: int | None
    unit_amount_cents: int | None
    price_id: str | None


class BillingService:
    """Encapsulates billing operations while hiding persistence details."""

    processor_name = "stripe"

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

    async def _upsert_billing_customer(
        self,
        *,
        tenant_id: str,
        customer_id: str,
        billing_email: str | None,
        processor: str | None = None,
    ) -> BillingCustomerRecord:
        repository = self._require_repository()
        record = BillingCustomerRecord(
            tenant_id=tenant_id,
            processor=processor or self.processor_name,
            processor_customer_id=customer_id,
            billing_email=billing_email,
        )
        try:
            return await repository.upsert_customer(record)
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc

    async def _resolve_customer_id(
        self,
        tenant_id: str,
        billing_email: str | None,
        *,
        create_if_missing: bool,
    ) -> str | None:
        record = await self._resolve_customer(
            tenant_id,
            billing_email,
            create_if_missing=create_if_missing,
        )
        return record.processor_customer_id if record else None

    async def _resolve_customer(
        self,
        tenant_id: str,
        billing_email: str | None,
        *,
        create_if_missing: bool,
    ) -> BillingCustomerRecord | None:
        repository = self._require_repository()
        try:
            subscription = await repository.get_subscription(tenant_id)
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc
        if subscription and subscription.processor_customer_id:
            effective_email = billing_email or subscription.billing_email
            if effective_email:
                return await self._upsert_billing_customer(
                    tenant_id=tenant_id,
                    customer_id=subscription.processor_customer_id,
                    billing_email=effective_email,
                )
            try:
                existing_record = await repository.get_customer(
                    tenant_id, processor=self.processor_name
                )
            except ValueError as exc:
                raise InvalidTenantIdentifierError(
                    "Tenant identifier is not a valid UUID."
                ) from exc
            if existing_record:
                return existing_record
            return await self._upsert_billing_customer(
                tenant_id=tenant_id,
                customer_id=subscription.processor_customer_id,
                billing_email=None,
            )

        try:
            customer_record = await repository.get_customer(
                tenant_id, processor=self.processor_name
            )
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc
        if customer_record:
            if billing_email and billing_email != customer_record.billing_email:
                return await self._upsert_billing_customer(
                    tenant_id=tenant_id,
                    customer_id=customer_record.processor_customer_id,
                    billing_email=billing_email,
                    processor=customer_record.processor,
                )
            return customer_record

        if not create_if_missing:
            return None

        try:
            provisioned = await self._gateway.create_customer(
                tenant_id=tenant_id,
                billing_email=billing_email,
            )
        except PaymentGatewayError as exc:
            raise PaymentProviderError(str(exc)) from exc

        return await self._upsert_billing_customer(
            tenant_id=tenant_id,
            customer_id=provisioned.customer_id,
            billing_email=billing_email,
            processor=provisioned.processor,
        )

    async def list_plans(self) -> list[BillingPlan]:
        return await self._require_repository().list_plans()

    async def get_plan(self, plan_code: str) -> BillingPlan:
        return await self._ensure_plan_exists(plan_code)

    async def get_subscription(self, tenant_id: str) -> TenantSubscription | None:
        try:
            return await self._require_repository().get_subscription(tenant_id)
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc

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
        resolved_seat_count = seat_count if seat_count is not None else plan.seat_included
        gateway_seat_count = resolved_seat_count if resolved_seat_count is not None else 1
        customer_record = await self._resolve_customer(
            tenant_id,
            billing_email,
            create_if_missing=False,
        )
        effective_billing_email = billing_email or (
            customer_record.billing_email if customer_record else None
        )
        existing_customer_id = (
            customer_record.processor_customer_id if customer_record else None
        )
        try:
            processor_payload = await self._gateway.start_subscription(
                tenant_id=tenant_id,
                plan_code=plan_code,
                billing_email=effective_billing_email,
                auto_renew=auto_renew,
                seat_count=gateway_seat_count,
                trial_days=trial_days,
                customer_id=existing_customer_id,
            )
        except PaymentGatewayError as exc:
            raise PaymentProviderError(str(exc)) from exc

        subscription = TenantSubscription(
            tenant_id=tenant_id,
            plan_code=plan_code,
            status="active",
            auto_renew=auto_renew,
            billing_email=effective_billing_email,
            starts_at=processor_payload.starts_at,
            current_period_start=processor_payload.current_period_start,
            current_period_end=processor_payload.current_period_end,
            trial_ends_at=processor_payload.trial_ends_at,
            seat_count=resolved_seat_count,
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

        await self._upsert_billing_customer(
            tenant_id=tenant_id,
            customer_id=processor_payload.customer_id,
            billing_email=effective_billing_email,
            processor=processor_payload.processor,
        )
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

        if updated.processor_customer_id:
            await self._upsert_billing_customer(
                tenant_id=tenant_id,
                customer_id=updated.processor_customer_id,
                billing_email=updated.billing_email,
            )
        return updated

    async def change_subscription_plan(
        self,
        *,
        tenant_id: str,
        plan_code: str,
        seat_count: int | None = None,
        timing: PlanChangeTiming = PlanChangeTiming.AUTO,
    ) -> PlanChangeResult:
        subscription = await self._require_subscription(tenant_id)
        current_plan = await self._ensure_plan_exists(subscription.plan_code)
        target_plan = await self._ensure_plan_exists(plan_code)

        if subscription.pending_plan_code == plan_code:
            raise SubscriptionStateError("A plan change is already scheduled for this plan.")
        if subscription.plan_code == plan_code:
            raise SubscriptionStateError("Subscription is already on the requested plan.")
        if not subscription.processor_subscription_id:
            raise SubscriptionStateError("Subscription is missing processor identifier.")

        effective_seat_count = (
            seat_count
            if seat_count is not None
            else subscription.seat_count
            or target_plan.seat_included
            or current_plan.seat_included
            or 1
        )
        current_seat_count = (
            subscription.seat_count
            if subscription.seat_count is not None
            else current_plan.seat_included
            or 1
        )
        resolved_timing = _resolve_plan_change_timing(
            timing,
            current_plan=current_plan,
            target_plan=target_plan,
            current_seat_count=current_seat_count,
            target_seat_count=effective_seat_count,
        )

        effective_at: datetime | None
        if resolved_timing == PlanChangeTiming.IMMEDIATE:
            try:
                swap_result = await self._gateway.swap_subscription_plan(
                    subscription.processor_subscription_id,
                    plan_code=plan_code,
                    seat_count=effective_seat_count,
                    schedule_id=subscription.processor_schedule_id,
                    proration_behavior="always_invoice",
                )
            except PaymentGatewayError as exc:
                raise PaymentProviderError(str(exc)) from exc

            subscription.plan_code = target_plan.code
            subscription.seat_count = effective_seat_count
            subscription.pending_plan_code = None
            subscription.pending_plan_effective_at = None
            subscription.pending_seat_count = None
            subscription.processor_schedule_id = None
            subscription.current_period_start = (
                swap_result.current_period_start or subscription.current_period_start
            )
            subscription.current_period_end = (
                swap_result.current_period_end or subscription.current_period_end
            )

            metadata = dict(subscription.metadata or {})
            metadata["processor_price_id"] = swap_result.price_id
            if swap_result.subscription_item_id:
                metadata["processor_subscription_item_id"] = swap_result.subscription_item_id
            subscription.metadata = metadata

            effective_at = datetime.now(UTC)
        else:
            try:
                schedule_result = await self._gateway.schedule_subscription_plan(
                    subscription.processor_subscription_id,
                    plan_code=plan_code,
                    seat_count=effective_seat_count,
                )
            except PaymentGatewayError as exc:
                raise PaymentProviderError(str(exc)) from exc

            subscription.pending_plan_code = plan_code
            subscription.pending_plan_effective_at = schedule_result.current_period_end
            subscription.pending_seat_count = effective_seat_count
            subscription.processor_schedule_id = schedule_result.schedule_id
            subscription.current_period_start = (
                schedule_result.current_period_start or subscription.current_period_start
            )
            subscription.current_period_end = (
                schedule_result.current_period_end or subscription.current_period_end
            )
            effective_at = subscription.pending_plan_effective_at

        try:
            await self._require_repository().upsert_subscription(subscription)
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc

        return PlanChangeResult(
            subscription=subscription,
            target_plan_code=plan_code,
            effective_at=effective_at,
            seat_count=effective_seat_count,
            timing=resolved_timing,
        )

    async def create_portal_session(
        self,
        tenant_id: str,
        *,
        billing_email: str | None = None,
    ) -> PortalSessionResult:
        customer_id = await self._resolve_customer_id(
            tenant_id,
            billing_email,
            create_if_missing=True,
        )
        if not customer_id:
            raise BillingCustomerNotFoundError("Billing customer not found.")
        settings = get_settings()
        return_url = settings.resolve_stripe_portal_return_url()
        try:
            return await self._gateway.create_portal_session(
                customer_id=customer_id,
                return_url=return_url,
            )
        except PaymentGatewayError as exc:
            raise PaymentProviderError(str(exc)) from exc

    async def list_payment_methods(
        self, tenant_id: str
    ) -> list[PaymentMethodSummary]:
        customer_id = await self._resolve_customer_id(
            tenant_id,
            billing_email=None,
            create_if_missing=False,
        )
        if not customer_id:
            return []
        try:
            return await self._gateway.list_payment_methods(customer_id=customer_id)
        except PaymentGatewayError as exc:
            raise PaymentProviderError(str(exc)) from exc

    async def create_setup_intent(
        self,
        tenant_id: str,
        *,
        billing_email: str | None = None,
    ) -> SetupIntentResult:
        customer_id = await self._resolve_customer_id(
            tenant_id,
            billing_email,
            create_if_missing=True,
        )
        if not customer_id:
            raise BillingCustomerNotFoundError("Billing customer not found.")
        try:
            return await self._gateway.create_setup_intent(customer_id=customer_id)
        except PaymentGatewayError as exc:
            raise PaymentProviderError(str(exc)) from exc

    async def set_default_payment_method(
        self,
        tenant_id: str,
        *,
        payment_method_id: str,
    ) -> None:
        customer_id = await self._resolve_customer_id(
            tenant_id,
            billing_email=None,
            create_if_missing=False,
        )
        if not customer_id:
            raise BillingCustomerNotFoundError("Billing customer not found.")
        try:
            await self._gateway.set_default_payment_method(
                customer_id=customer_id,
                payment_method_id=payment_method_id,
            )
        except PaymentGatewayError as exc:
            raise PaymentProviderError(str(exc)) from exc

    async def detach_payment_method(
        self,
        tenant_id: str,
        *,
        payment_method_id: str,
    ) -> None:
        customer_id = await self._resolve_customer_id(
            tenant_id,
            billing_email=None,
            create_if_missing=False,
        )
        if not customer_id:
            raise BillingCustomerNotFoundError("Billing customer not found.")
        try:
            await self._gateway.detach_payment_method(
                customer_id=customer_id,
                payment_method_id=payment_method_id,
            )
        except PaymentGatewayError as exc:
            raise PaymentProviderError(str(exc)) from exc

    async def preview_upcoming_invoice(
        self,
        tenant_id: str,
        *,
        seat_count: int | None,
    ) -> UpcomingInvoicePreview:
        subscription = await self._require_subscription(tenant_id)
        if not subscription.processor_subscription_id:
            raise SubscriptionStateError("Subscription is missing processor identifier.")

        plan = await self._ensure_plan_exists(subscription.plan_code)
        effective_seat_count = (
            seat_count
            if seat_count is not None
            else subscription.seat_count or plan.seat_included
        )

        try:
            preview = await self._gateway.preview_upcoming_invoice(
                subscription_id=subscription.processor_subscription_id,
                seat_count=effective_seat_count,
            )
        except PaymentGatewayError as exc:
            raise PaymentProviderError(str(exc)) from exc

        return UpcomingInvoicePreview(
            plan_code=subscription.plan_code,
            plan_name=plan.name,
            seat_count=effective_seat_count,
            invoice_id=preview.invoice_id,
            amount_due_cents=preview.amount_due_cents,
            currency=preview.currency,
            period_start=preview.period_start,
            period_end=preview.period_end,
            lines=[
                UpcomingInvoiceLineSnapshot(
                    description=line.description,
                    amount_cents=line.amount_cents,
                    currency=line.currency,
                    quantity=line.quantity,
                    unit_amount_cents=line.unit_amount_cents,
                    price_id=line.price_id,
                )
                for line in preview.lines
            ],
        )

    async def sync_subscription_from_processor(
        self,
        snapshot: ProcessorSubscriptionSnapshot,
        *,
        processor_name: str = "stripe",
    ) -> TenantSubscription:
        repository = self._require_repository()
        try:
            existing = await repository.get_subscription(snapshot.tenant_id)
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc

        starts_at = snapshot.starts_at or datetime.now(UTC)
        plan = await self._ensure_plan_exists(snapshot.plan_code)
        merged_metadata = _merge_subscription_metadata(
            existing.metadata if existing else None,
            snapshot.metadata,
        )
        pending_plan_code = existing.pending_plan_code if existing else None
        pending_effective_at = existing.pending_plan_effective_at if existing else None
        pending_seat_count = existing.pending_seat_count if existing else None
        schedule_id = snapshot.processor_schedule_id

        if not schedule_id:
            pending_plan_code = None
            pending_effective_at = None
            pending_seat_count = None
        elif pending_plan_code and pending_plan_code == snapshot.plan_code:
            pending_plan_code = None
            pending_effective_at = None
            pending_seat_count = None

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
            pending_plan_code=pending_plan_code,
            pending_plan_effective_at=pending_effective_at,
            pending_seat_count=pending_seat_count,
            metadata=merged_metadata,
            processor=processor_name,
            processor_customer_id=snapshot.processor_customer_id,
            processor_subscription_id=snapshot.processor_subscription_id,
            processor_schedule_id=schedule_id,
        )
        try:
            await repository.upsert_subscription(subscription)
        except ValueError as exc:
            raise InvalidTenantIdentifierError("Tenant identifier is not a valid UUID.") from exc

        if snapshot.processor_customer_id:
            await self._upsert_billing_customer(
                tenant_id=snapshot.tenant_id,
                customer_id=snapshot.processor_customer_id,
                billing_email=snapshot.billing_email,
                processor=processor_name,
            )
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


def _merge_subscription_metadata(
    existing: dict[str, str] | None,
    incoming: dict[str, str] | None,
) -> dict[str, str]:
    merged: dict[str, str] = dict(existing or {})
    reserved_keys = {
        "pending_plan_code",
        "pending_plan_effective_at",
        "pending_seat_count",
        "processor_schedule_id",
    }
    if incoming:
        for key, value in incoming.items():
            if value is None:
                continue
            key_str = str(key)
            if key_str in reserved_keys:
                continue
            merged[key_str] = str(value)

    for reserved in reserved_keys:
        merged.pop(reserved, None)

    return merged


def _resolve_plan_change_timing(
    timing: PlanChangeTiming,
    *,
    current_plan: BillingPlan,
    target_plan: BillingPlan,
    current_seat_count: int,
    target_seat_count: int,
) -> PlanChangeTiming:
    if timing != PlanChangeTiming.AUTO:
        return timing
    if (
        current_plan.interval == target_plan.interval
        and current_plan.interval_count == target_plan.interval_count
    ):
        current_total = current_plan.price_cents * max(current_seat_count, 1)
        target_total = target_plan.price_cents * max(target_seat_count, 1)
        if target_total > current_total:
            return PlanChangeTiming.IMMEDIATE
        return PlanChangeTiming.PERIOD_END
    return PlanChangeTiming.PERIOD_END


def get_billing_service() -> BillingService:
    """Resolve the active billing service from the application container."""

    from app.bootstrap.container import get_container

    return get_container().billing_service


class _BillingServiceHandle:
    """Proxy exposing the container-backed billing service."""

    def __getattr__(self, name: str):
        return getattr(get_billing_service(), name)


billing_service = _BillingServiceHandle()
