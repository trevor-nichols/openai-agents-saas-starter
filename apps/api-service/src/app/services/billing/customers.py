"""Customer and payment-method orchestration for billing."""

from __future__ import annotations

from collections.abc import Callable

from app.core.settings import Settings, get_settings
from app.domain.billing import BillingCustomerRecord
from app.services.billing.context import BillingContext
from app.services.billing.errors import (
    BillingCustomerNotFoundError,
    raise_invalid_tenant,
    raise_payment_provider,
)
from app.services.billing.payment_gateway import (
    PaymentGatewayError,
    PaymentMethodSummary,
    PortalSessionResult,
    SetupIntentResult,
)


class BillingCustomerService:
    """Coordinates billing customers with the payment gateway."""

    def __init__(
        self,
        context: BillingContext,
        *,
        settings_provider: Callable[[], Settings] = get_settings,
        processor_name: str = "stripe",
    ) -> None:
        self._context = context
        self._settings_provider = settings_provider
        self._processor_name = processor_name

    async def upsert_customer_record(
        self,
        *,
        tenant_id: str,
        customer_id: str,
        billing_email: str | None,
        processor: str | None = None,
    ) -> BillingCustomerRecord:
        repository = self._context.require_repository()
        record = BillingCustomerRecord(
            tenant_id=tenant_id,
            processor=processor or self._processor_name,
            processor_customer_id=customer_id,
            billing_email=billing_email,
        )
        try:
            return await repository.upsert_customer(record)
        except ValueError as exc:
            raise_invalid_tenant(exc)

    async def resolve_customer_id(
        self,
        tenant_id: str,
        billing_email: str | None,
        *,
        create_if_missing: bool,
    ) -> str | None:
        record = await self.resolve_customer(
            tenant_id,
            billing_email,
            create_if_missing=create_if_missing,
        )
        return record.processor_customer_id if record else None

    async def resolve_customer(
        self,
        tenant_id: str,
        billing_email: str | None,
        *,
        create_if_missing: bool,
    ) -> BillingCustomerRecord | None:
        repository = self._context.require_repository()
        try:
            subscription = await repository.get_subscription(tenant_id)
        except ValueError as exc:
            raise_invalid_tenant(exc)
        if subscription and subscription.processor_customer_id:
            effective_email = billing_email or subscription.billing_email
            if effective_email:
                return await self.upsert_customer_record(
                    tenant_id=tenant_id,
                    customer_id=subscription.processor_customer_id,
                    billing_email=effective_email,
                )
            try:
                existing_record = await repository.get_customer(
                    tenant_id, processor=self._processor_name
                )
            except ValueError as exc:
                raise_invalid_tenant(exc)
            if existing_record:
                return existing_record
            return await self.upsert_customer_record(
                tenant_id=tenant_id,
                customer_id=subscription.processor_customer_id,
                billing_email=None,
            )

        try:
            customer_record = await repository.get_customer(
                tenant_id, processor=self._processor_name
            )
        except ValueError as exc:
            raise_invalid_tenant(exc)
        if customer_record:
            if billing_email and billing_email != customer_record.billing_email:
                return await self.upsert_customer_record(
                    tenant_id=tenant_id,
                    customer_id=customer_record.processor_customer_id,
                    billing_email=billing_email,
                    processor=customer_record.processor,
                )
            return customer_record

        if not create_if_missing:
            return None

        try:
            provisioned = await self._context.require_gateway().create_customer(
                tenant_id=tenant_id,
                billing_email=billing_email,
            )
        except PaymentGatewayError as exc:
            raise_payment_provider(exc)

        return await self.upsert_customer_record(
            tenant_id=tenant_id,
            customer_id=provisioned.customer_id,
            billing_email=billing_email,
            processor=provisioned.processor,
        )

    async def create_portal_session(
        self,
        tenant_id: str,
        *,
        billing_email: str | None = None,
    ) -> PortalSessionResult:
        customer_id = await self.resolve_customer_id(
            tenant_id,
            billing_email,
            create_if_missing=True,
        )
        if not customer_id:
            raise BillingCustomerNotFoundError("Billing customer not found.")
        settings = self._settings_provider()
        return_url = settings.resolve_stripe_portal_return_url()
        try:
            return await self._context.require_gateway().create_portal_session(
                customer_id=customer_id,
                return_url=return_url,
            )
        except PaymentGatewayError as exc:
            raise_payment_provider(exc)

    async def list_payment_methods(self, tenant_id: str) -> list[PaymentMethodSummary]:
        customer_id = await self.resolve_customer_id(
            tenant_id,
            billing_email=None,
            create_if_missing=False,
        )
        if not customer_id:
            return []
        try:
            return await self._context.require_gateway().list_payment_methods(
                customer_id=customer_id
            )
        except PaymentGatewayError as exc:
            raise_payment_provider(exc)

    async def create_setup_intent(
        self,
        tenant_id: str,
        *,
        billing_email: str | None = None,
    ) -> SetupIntentResult:
        customer_id = await self.resolve_customer_id(
            tenant_id,
            billing_email,
            create_if_missing=True,
        )
        if not customer_id:
            raise BillingCustomerNotFoundError("Billing customer not found.")
        try:
            return await self._context.require_gateway().create_setup_intent(
                customer_id=customer_id
            )
        except PaymentGatewayError as exc:
            raise_payment_provider(exc)

    async def set_default_payment_method(
        self,
        tenant_id: str,
        *,
        payment_method_id: str,
    ) -> None:
        customer_id = await self.resolve_customer_id(
            tenant_id,
            billing_email=None,
            create_if_missing=False,
        )
        if not customer_id:
            raise BillingCustomerNotFoundError("Billing customer not found.")
        try:
            await self._context.require_gateway().set_default_payment_method(
                customer_id=customer_id,
                payment_method_id=payment_method_id,
            )
        except PaymentGatewayError as exc:
            raise_payment_provider(exc)

    async def detach_payment_method(
        self,
        tenant_id: str,
        *,
        payment_method_id: str,
    ) -> None:
        customer_id = await self.resolve_customer_id(
            tenant_id,
            billing_email=None,
            create_if_missing=False,
        )
        if not customer_id:
            raise BillingCustomerNotFoundError("Billing customer not found.")
        try:
            await self._context.require_gateway().detach_payment_method(
                customer_id=customer_id,
                payment_method_id=payment_method_id,
            )
        except PaymentGatewayError as exc:
            raise_payment_provider(exc)


__all__ = ["BillingCustomerService"]
