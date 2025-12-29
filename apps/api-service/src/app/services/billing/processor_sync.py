"""Processor-driven synchronization for subscriptions and invoices."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.billing import SubscriptionInvoiceRecord, TenantSubscription
from app.services.billing.context import BillingContext
from app.services.billing.customers import BillingCustomerService
from app.services.billing.errors import raise_invalid_tenant
from app.services.billing.models import ProcessorInvoiceSnapshot, ProcessorSubscriptionSnapshot
from app.services.billing.policies import merge_subscription_metadata
from app.services.billing.queries import ensure_plan_exists
from app.services.billing.utils import to_utc


class BillingProcessorSyncService:
    """Synchronizes processor snapshots into local billing state."""

    def __init__(self, context: BillingContext, *, customers: BillingCustomerService) -> None:
        self._context = context
        self._customers = customers

    async def sync_subscription_from_processor(
        self,
        snapshot: ProcessorSubscriptionSnapshot,
        *,
        processor_name: str = "stripe",
    ) -> TenantSubscription:
        repository = self._context.require_repository()
        try:
            existing = await repository.get_subscription(snapshot.tenant_id)
        except ValueError as exc:
            raise_invalid_tenant(exc)

        starts_at = snapshot.starts_at or datetime.now(UTC)
        plan = await ensure_plan_exists(repository, snapshot.plan_code)
        merged_metadata = merge_subscription_metadata(
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
            raise_invalid_tenant(exc)

        if snapshot.processor_customer_id:
            await self._customers.upsert_customer_record(
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
        repository = self._context.require_repository()
        period_start = to_utc(snapshot.period_start or datetime.now(UTC))
        period_end = to_utc(snapshot.period_end or period_start)
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
            raise_invalid_tenant(exc)

        for line in snapshot.lines:
            if not line.feature_key or line.quantity in (None, 0):
                continue
            line_start = to_utc(line.period_start) if line.period_start else period_start
            line_end = to_utc(line.period_end) if line.period_end else period_end
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
                raise_invalid_tenant(exc)


__all__ = ["BillingProcessorSyncService"]
