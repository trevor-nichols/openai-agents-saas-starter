"""Normalize persisted Stripe events into billing stream payloads."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.infrastructure.persistence.stripe.models import StripeEvent
from app.services.billing.stripe.event_models import (
    DispatchBroadcastContext,
    InvoiceSnapshotView,
    SubscriptionSnapshotView,
    UsageDelta,
)

from .payloads import (
    BillingEventInvoice,
    BillingEventPayload,
    BillingEventSubscription,
    BillingEventUsage,
)
from .types import JSONDict


class BillingEventNormalizer:
    """Pure helper that converts Stripe events into billing payloads."""

    def normalize(
        self,
        record: StripeEvent,
        payload: JSONDict,
        context: DispatchBroadcastContext | None,
    ) -> BillingEventPayload | None:
        tenant_id = context.tenant_id if context else record.tenant_hint
        if tenant_id is None:
            return None
        data_container = _as_dict(payload.get("data"))
        data_object = _as_dict(data_container.get("object"))
        context_status = context.status if context else None
        context_summary = context.summary if context else None
        status = context_status or data_object.get("status") or data_object.get("billing_reason")
        summary = context_summary or data_object.get("description") or status
        occurred_at = record.processed_at or record.received_at
        subscription = None
        invoice = None
        usage: list[BillingEventUsage] = []
        if context:
            if context.subscription:
                subscription = self._subscription_payload_from_context(context.subscription)
            if context.invoice:
                invoice = self._invoice_payload_from_context(context.invoice)
            if context.usage:
                usage = [self._usage_payload_from_context(item) for item in context.usage]

        if subscription is None or invoice is None or not usage:
            (
                derived_subscription,
                derived_invoice,
                derived_usage,
            ) = self._derive_artifacts_from_payload(record.event_type, data_object)
            if subscription is None:
                subscription = derived_subscription
            if invoice is None:
                invoice = derived_invoice
            if not usage:
                usage = derived_usage
        return BillingEventPayload(
            tenant_id=tenant_id,
            event_type=record.event_type,
            stripe_event_id=record.stripe_event_id,
            occurred_at=(occurred_at or datetime.now(UTC)).isoformat(),
            summary=summary,
            status=status or record.processing_outcome,
            subscription=subscription,
            invoice=invoice,
            usage=usage,
        )

    def _derive_artifacts_from_payload(
        self, event_type: str, data_object: JSONDict
    ) -> tuple[
        BillingEventSubscription | None,
        BillingEventInvoice | None,
        list[BillingEventUsage],
    ]:
        subscription = None
        invoice = None
        usage: list[BillingEventUsage] = []
        normalized_type = event_type or ""
        if normalized_type.startswith("customer.subscription"):
            subscription = self._subscription_payload_from_object(data_object)
        if normalized_type.startswith("invoice."):
            invoice = self._invoice_payload_from_object(data_object)
            usage = self._usage_from_invoice_object(data_object)
        return subscription, invoice, usage

    def _subscription_payload_from_object(
        self, data_obj: JSONDict
    ) -> BillingEventSubscription | None:
        if not data_obj:
            return None
        plan_code = self._extract_plan_code(data_obj) or "unknown-plan"
        quantity = self._extract_quantity(data_obj)
        return BillingEventSubscription(
            plan_code=plan_code,
            status=str(data_obj.get("status") or "unknown"),
            seat_count=quantity,
            auto_renew=not bool(data_obj.get("cancel_at_period_end")),
            current_period_start=self._iso(
                self._coerce_datetime(data_obj.get("current_period_start"))
            ),
            current_period_end=self._iso(
                self._coerce_datetime(data_obj.get("current_period_end"))
            ),
            trial_ends_at=self._iso(self._coerce_datetime(data_obj.get("trial_end"))),
            cancel_at=self._iso(self._coerce_datetime(data_obj.get("cancel_at"))),
        )

    def _invoice_payload_from_object(self, invoice_obj: JSONDict) -> BillingEventInvoice | None:
        if not invoice_obj:
            return None
        amount_due = invoice_obj.get("amount_due")
        if amount_due is None:
            amount_due = invoice_obj.get("total")
        amount_value = self._coerce_int(amount_due, default=0)
        return BillingEventInvoice(
            invoice_id=str(invoice_obj.get("id") or "invoice"),
            status=str(invoice_obj.get("status") or "unknown"),
            amount_due_cents=amount_value,
            currency=str(invoice_obj.get("currency") or "usd"),
            billing_reason=invoice_obj.get("billing_reason"),
            hosted_invoice_url=
                invoice_obj.get("hosted_invoice_url") or invoice_obj.get("invoice_pdf"),
            collection_method=invoice_obj.get("collection_method"),
            period_start=self._iso(self._coerce_datetime(invoice_obj.get("period_start"))),
            period_end=self._iso(self._coerce_datetime(invoice_obj.get("period_end"))),
        )

    def _usage_from_invoice_object(self, invoice_obj: JSONDict) -> list[BillingEventUsage]:
        lines = ((invoice_obj.get("lines") or {}).get("data")) or []
        usage_entries: list[BillingEventUsage] = []
        for index, line in enumerate(lines):
            price = line.get("price") or {}
            recurring = price.get("recurring") or {}
            metadata = {
                **(price.get("metadata") or {}),
                **(line.get("metadata") or {}),
            }
            usage_type = recurring.get("usage_type")
            is_metered = usage_type == "metered" or bool(line.get("usage_record_summary"))
            if not is_metered:
                continue
            feature_key = (
                metadata.get("feature_key")
                or metadata.get("plan_feature")
                or price.get("nickname")
                or line.get("description")
                or f"feature-{index}"
            )
            quantity_raw = line.get("quantity")
            if quantity_raw in (None, 0):
                summary = line.get("usage_record_summary") or {}
                quantity_raw = summary.get("total_usage")
            quantity = self._maybe_int(quantity_raw)
            if quantity is None:
                continue
            period = line.get("period") or {}
            usage_entries.append(
                BillingEventUsage(
                    feature_key=str(feature_key),
                    quantity=quantity,
                    period_start=self._iso(self._coerce_datetime(period.get("start"))),
                    period_end=self._iso(self._coerce_datetime(period.get("end"))),
                    amount_cents=self._coerce_int(line.get("amount"), default=0),
                )
            )
        return usage_entries

    def _extract_plan_code(self, data_obj: JSONDict) -> str | None:
        items = ((data_obj.get("items") or {}).get("data")) or []
        if items:
            price = items[0].get("price") or {}
            metadata = price.get("metadata") or {}
            return (
                metadata.get("plan_code")
                or metadata.get("starter_console_plan_code")
                or price.get("nickname")
                or price.get("id")
            )
        plan = data_obj.get("plan") or {}
        metadata = plan.get("metadata") or {}
        return (
            metadata.get("plan_code")
            or metadata.get("starter_console_plan_code")
            or plan.get("nickname")
            or plan.get("id")
        )

    def _extract_quantity(self, data_obj: JSONDict) -> int | None:
        items = ((data_obj.get("items") or {}).get("data")) or []
        if items:
            quantity = items[0].get("quantity")
            quantity_val = self._maybe_int(quantity)
            if quantity_val is not None:
                return quantity_val
        quantity = data_obj.get("quantity")
        return self._maybe_int(quantity)

    def _subscription_payload_from_context(
        self, view: SubscriptionSnapshotView
    ) -> BillingEventSubscription:
        return BillingEventSubscription(
            plan_code=view.plan_code,
            status=view.status,
            seat_count=view.seat_count,
            auto_renew=view.auto_renew,
            current_period_start=self._iso(view.current_period_start),
            current_period_end=self._iso(view.current_period_end),
            trial_ends_at=self._iso(view.trial_ends_at),
            cancel_at=self._iso(view.cancel_at),
        )

    def _invoice_payload_from_context(self, view: InvoiceSnapshotView) -> BillingEventInvoice:
        return BillingEventInvoice(
            invoice_id=view.invoice_id,
            status=view.status,
            amount_due_cents=view.amount_due_cents,
            currency=view.currency,
            billing_reason=view.billing_reason,
            hosted_invoice_url=view.hosted_invoice_url,
            collection_method=view.collection_method,
            period_start=self._iso(view.period_start),
            period_end=self._iso(view.period_end),
        )

    def _usage_payload_from_context(self, usage: UsageDelta) -> BillingEventUsage:
        return BillingEventUsage(
            feature_key=usage.feature_key,
            quantity=usage.quantity,
            period_start=self._iso(usage.period_start),
            period_end=self._iso(usage.period_end),
            amount_cents=usage.amount_cents,
        )

    @staticmethod
    def _iso(value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        else:
            value = value.astimezone(UTC)
        return value.isoformat()

    @staticmethod
    def _coerce_datetime(value: Any) -> datetime | None:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        try:
            return datetime.fromtimestamp(float(value), tz=UTC)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _coerce_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _maybe_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


def _as_dict(value: Any) -> JSONDict:
    return value if isinstance(value, dict) else {}
