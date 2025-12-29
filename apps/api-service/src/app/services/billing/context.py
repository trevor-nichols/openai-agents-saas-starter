"""Shared dependency context for billing services."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.billing import BillingRepository
from app.services.billing.payment_gateway import PaymentGateway


@dataclass(slots=True)
class BillingContext:
    repository: BillingRepository | None = None
    gateway: PaymentGateway | None = None

    def require_repository(self) -> BillingRepository:
        if self.repository is None:
            raise RuntimeError("Billing repository has not been configured.")
        return self.repository

    def require_gateway(self) -> PaymentGateway:
        if self.gateway is None:
            raise RuntimeError("Billing gateway has not been configured.")
        return self.gateway


__all__ = ["BillingContext"]
