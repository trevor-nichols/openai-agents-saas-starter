"""Invoice query services for billing."""

from __future__ import annotations

from app.domain.billing import SubscriptionInvoiceRecord
from app.services.billing.context import BillingContext
from app.services.billing.errors import raise_invalid_tenant


class BillingInvoiceService:
    """Provides read-only access to persisted subscription invoices."""

    def __init__(self, context: BillingContext) -> None:
        self._context = context

    async def list_invoices(
        self,
        tenant_id: str,
        *,
        limit: int,
        offset: int,
    ) -> list[SubscriptionInvoiceRecord]:
        repository = self._context.require_repository()
        try:
            return await repository.list_invoices(tenant_id, limit=limit, offset=offset)
        except ValueError as exc:
            raise_invalid_tenant(exc)

    async def get_invoice(
        self,
        tenant_id: str,
        *,
        invoice_id: str,
    ) -> SubscriptionInvoiceRecord | None:
        repository = self._context.require_repository()
        try:
            return await repository.get_invoice(tenant_id, invoice_id=invoice_id)
        except ValueError as exc:
            raise_invalid_tenant(exc)


__all__ = ["BillingInvoiceService"]
