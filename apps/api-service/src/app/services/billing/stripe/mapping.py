"""Mapping helpers from Stripe models to gateway DTOs."""

from __future__ import annotations

from app.infrastructure.stripe import StripePaymentMethodList, StripeUpcomingInvoice
from app.services.billing.payment_gateway import (
    PaymentMethodSummary,
    UpcomingInvoiceLine,
    UpcomingInvoicePreviewResult,
)


def build_payment_method_summaries(
    methods: StripePaymentMethodList,
) -> list[PaymentMethodSummary]:
    default_id = methods.default_payment_method_id
    return [
        PaymentMethodSummary(
            id=item.id,
            brand=item.brand,
            last4=item.last4,
            exp_month=item.exp_month,
            exp_year=item.exp_year,
            is_default=item.id == default_id,
        )
        for item in methods.items
    ]


def build_upcoming_invoice_preview(
    invoice: StripeUpcomingInvoice,
) -> UpcomingInvoicePreviewResult:
    lines = [
        UpcomingInvoiceLine(
            description=line.description,
            amount_cents=line.amount,
            currency=line.currency,
            quantity=line.quantity,
            unit_amount_cents=line.unit_amount,
            price_id=line.price_id,
        )
        for line in invoice.lines
    ]
    return UpcomingInvoicePreviewResult(
        invoice_id=invoice.id,
        amount_due_cents=invoice.amount_due,
        currency=invoice.currency,
        period_start=invoice.period_start,
        period_end=invoice.period_end,
        lines=lines,
    )


__all__ = ["build_payment_method_summaries", "build_upcoming_invoice_preview"]
