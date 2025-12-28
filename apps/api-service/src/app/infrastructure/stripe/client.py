"""Typed Stripe client wrappers with retries and error translation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.infrastructure.stripe.errors import StripeClientError
from app.infrastructure.stripe.mappers import (
    extract_default_payment_method_id,
    extract_payment_method_customer_id,
    iter_items,
    to_datetime,
    to_invoice_line,
    to_payment_method,
    to_schedule,
    to_subscription,
)
from app.infrastructure.stripe.models import (
    StripeCustomer,
    StripePaymentMethodDetail,
    StripePaymentMethodList,
    StripePortalSession,
    StripeSetupIntent,
    StripeSubscription,
    StripeSubscriptionSchedule,
    StripeUpcomingInvoice,
    StripeUsageRecord,
)
from app.infrastructure.stripe.sdk import (
    SUBSCRIPTION_EXPAND_FIELDS,
    configure_stripe_sdk,
    create_billing_portal_session,
    create_customer,
    create_setup_intent,
    create_subscription,
    create_subscription_schedule,
    create_usage_record,
    delete_subscription,
    detach_payment_method,
    list_payment_methods,
    modify_customer,
    modify_subscription,
    modify_subscription_schedule,
    preview_upcoming_invoice,
    release_subscription_schedule,
    retrieve_customer,
    retrieve_payment_method,
    retrieve_subscription,
    retrieve_subscription_schedule,
    set_default_payment_method,
)
from app.infrastructure.stripe.transport import StripeRequestExecutor
from app.infrastructure.stripe.types import (
    SubscriptionCreateParams,
    SubscriptionModifyItemPayload,
    SubscriptionModifyParams,
    SubscriptionScheduleCreateParams,
    SubscriptionScheduleModifyParams,
    SubscriptionSchedulePhasePayload,
    UsageRecordPayload,
)


class StripeClient:
    """Lightweight async-friendly Stripe wrapper with retries and metrics."""

    def __init__(
        self,
        api_key: str,
        *,
        max_attempts: int = 3,
        initial_backoff_seconds: float = 0.5,
    ) -> None:
        if not api_key:
            raise StripeClientError("config", "Stripe secret key is required.")
        self._executor = StripeRequestExecutor(
            max_attempts=max_attempts,
            initial_backoff_seconds=initial_backoff_seconds,
        )
        configure_stripe_sdk(api_key)

    async def create_customer(self, *, email: str | None, tenant_id: str) -> StripeCustomer:
        payload: dict[str, Any] = {
            "metadata": {"tenant_id": tenant_id},
            "description": f"Tenant {tenant_id}",
        }
        if email:
            payload["email"] = email

        customer = await self._executor.request(
            "customer.create",
            lambda: create_customer(payload),
        )
        return StripeCustomer(id=customer.id, email=customer.email)

    async def create_subscription(
        self,
        *,
        customer_id: str,
        price_id: str,
        quantity: int,
        auto_renew: bool,
        trial_period_days: int | None = None,
        metadata: dict[str, str] | None = None,
    ) -> StripeSubscription:
        params: SubscriptionCreateParams = {
            "customer": customer_id,
            "items": [
                {
                    "price": price_id,
                    "quantity": quantity,
                }
            ],
            "metadata": metadata or {},
            "expand": SUBSCRIPTION_EXPAND_FIELDS,
        }
        if not auto_renew:
            params["cancel_at_period_end"] = True
        if trial_period_days:
            params["trial_period_days"] = trial_period_days

        subscription = await self._executor.request(
            "subscription.create",
            lambda: create_subscription(params),
        )
        return to_subscription(subscription)

    async def retrieve_subscription(self, subscription_id: str) -> StripeSubscription:
        subscription = await self._executor.request(
            "subscription.retrieve",
            lambda: retrieve_subscription(subscription_id),
        )
        return to_subscription(subscription)

    async def modify_subscription(
        self,
        subscription: StripeSubscription,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
        price_id: str | None = None,
        metadata: dict[str, str] | None = None,
        proration_behavior: str | None = None,
    ) -> StripeSubscription:
        params: SubscriptionModifyParams = {"expand": SUBSCRIPTION_EXPAND_FIELDS}
        if auto_renew is not None:
            params["cancel_at_period_end"] = not auto_renew
        if seat_count is not None or price_id is not None:
            item = subscription.primary_item
            if item is None:
                raise StripeClientError(
                    "subscription.modify", "Subscription has no items to update quantity."
                )
            items: list[SubscriptionModifyItemPayload] = params.setdefault("items", [])
            payload: SubscriptionModifyItemPayload = {"id": item.id}
            if seat_count is not None:
                payload["quantity"] = seat_count
            if price_id is not None:
                payload["price"] = price_id
            items.append(payload)

        if metadata is not None:
            params["metadata"] = metadata
        if proration_behavior is not None:
            params["proration_behavior"] = proration_behavior

        if len(params) == 1:  # only expand present
            return subscription

        updated = await self._executor.request(
            "subscription.modify",
            lambda: modify_subscription(subscription.id, dict(params)),
        )
        return to_subscription(updated)

    async def cancel_subscription(
        self, subscription_id: str, *, cancel_at_period_end: bool
    ) -> StripeSubscription:
        params: dict[str, Any] = {
            "expand": SUBSCRIPTION_EXPAND_FIELDS,
        }
        if cancel_at_period_end:

            def cancel_fn() -> Any:
                updated_params = params | {"cancel_at_period_end": True}
                return modify_subscription(subscription_id, updated_params)

        else:

            def cancel_fn() -> Any:
                return delete_subscription(subscription_id, params)

        subscription = await self._executor.request("subscription.cancel", cancel_fn)
        return to_subscription(subscription)

    async def update_customer_email(self, customer_id: str, email: str) -> StripeCustomer:
        customer = await self._executor.request(
            "customer.modify",
            lambda: modify_customer(customer_id, email=email),
        )
        return StripeCustomer(id=customer.id, email=customer.email)

    async def create_subscription_schedule_from_subscription(
        self,
        subscription_id: str,
        *,
        end_behavior: str = "release",
    ) -> StripeSubscriptionSchedule:
        payload: SubscriptionScheduleCreateParams = {
            "from_subscription": subscription_id,
            "end_behavior": end_behavior,
        }
        schedule = await self._executor.request(
            "subscription_schedule.create",
            lambda: create_subscription_schedule(payload),
        )
        return to_schedule(schedule)

    async def retrieve_subscription_schedule(
        self, schedule_id: str
    ) -> StripeSubscriptionSchedule:
        schedule = await self._executor.request(
            "subscription_schedule.retrieve",
            lambda: retrieve_subscription_schedule(schedule_id),
        )
        return to_schedule(schedule)

    async def update_subscription_schedule(
        self,
        schedule_id: str,
        *,
        phases: list[SubscriptionSchedulePhasePayload],
        end_behavior: str | None = None,
        proration_behavior: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> StripeSubscriptionSchedule:
        params: SubscriptionScheduleModifyParams = {"phases": phases}
        if end_behavior is not None:
            params["end_behavior"] = end_behavior
        if proration_behavior is not None:
            params["proration_behavior"] = proration_behavior
        if metadata is not None:
            params["metadata"] = metadata

        schedule = await self._executor.request(
            "subscription_schedule.modify",
            lambda: modify_subscription_schedule(schedule_id, dict(params)),
        )
        return to_schedule(schedule)

    async def release_subscription_schedule(
        self,
        schedule_id: str,
    ) -> StripeSubscriptionSchedule:
        schedule = await self._executor.request(
            "subscription_schedule.release",
            lambda: release_subscription_schedule(schedule_id),
        )
        return to_schedule(schedule)

    async def create_usage_record(
        self,
        subscription_item_id: str,
        *,
        quantity: int,
        timestamp: int,
        idempotency_key: str,
        feature_key: str,
    ) -> StripeUsageRecord:
        request_payload: UsageRecordPayload = {
            "subscription_item_id": subscription_item_id,
            "quantity": quantity,
            "timestamp": timestamp,
            "idempotency_key": idempotency_key,
            "feature_key": feature_key,
        }
        record = await self._executor.request(
            "usage_record.create",
            lambda: create_usage_record(request_payload),
        )
        ts = to_datetime(record.timestamp)
        return StripeUsageRecord(
            id=record.id,
            subscription_item_id=record.subscription_item,
            quantity=record.quantity,
            timestamp=ts or datetime.now(UTC),
        )

    async def create_billing_portal_session(
        self, *, customer_id: str, return_url: str
    ) -> StripePortalSession:
        session = await self._executor.request(
            "billing_portal.create",
            lambda: create_billing_portal_session(customer_id, return_url),
        )
        return StripePortalSession(url=session.url)

    async def list_payment_methods(self, customer_id: str) -> StripePaymentMethodList:
        payment_methods = await self._executor.request(
            "payment_method.list",
            lambda: list_payment_methods(customer_id),
        )
        customer = await self._executor.request(
            "customer.retrieve",
            lambda: retrieve_customer(customer_id),
        )
        default_id = extract_default_payment_method_id(customer)
        items = [to_payment_method(method) for method in iter_items(payment_methods)]
        return StripePaymentMethodList(items=items, default_payment_method_id=default_id)

    async def retrieve_payment_method(
        self, payment_method_id: str
    ) -> StripePaymentMethodDetail:
        method = await self._executor.request(
            "payment_method.retrieve",
            lambda: retrieve_payment_method(payment_method_id),
        )
        return StripePaymentMethodDetail(
            id=method.id,
            customer_id=extract_payment_method_customer_id(method),
        )

    async def create_setup_intent(self, customer_id: str) -> StripeSetupIntent:
        intent = await self._executor.request(
            "setup_intent.create",
            lambda: create_setup_intent(customer_id),
        )
        return StripeSetupIntent(id=intent.id, client_secret=getattr(intent, "client_secret", None))

    async def set_default_payment_method(
        self, *, customer_id: str, payment_method_id: str
    ) -> None:
        await self._executor.request(
            "customer.set_default_payment_method",
            lambda: set_default_payment_method(customer_id, payment_method_id),
        )

    async def detach_payment_method(self, payment_method_id: str) -> None:
        await self._executor.request(
            "payment_method.detach",
            lambda: detach_payment_method(payment_method_id),
        )

    async def preview_upcoming_invoice(
        self,
        *,
        customer_id: str,
        subscription_id: str,
        subscription_item_id: str | None,
        seat_count: int | None,
        proration_behavior: str | None = None,
    ) -> StripeUpcomingInvoice:
        params: dict[str, Any] = {
            "customer": customer_id,
            "subscription": subscription_id,
        }
        if subscription_item_id and seat_count:
            params["subscription_items"] = [
                {"id": subscription_item_id, "quantity": seat_count}
            ]
        if proration_behavior:
            params["subscription_proration_behavior"] = proration_behavior

        invoice = await self._executor.request(
            "invoice.upcoming",
            lambda: preview_upcoming_invoice(params),
        )
        lines = [to_invoice_line(item) for item in iter_items(invoice.lines)]
        amount_due = getattr(invoice, "amount_due", None)
        if amount_due is None:
            amount_due = getattr(invoice, "total", 0)
        return StripeUpcomingInvoice(
            id=getattr(invoice, "id", None),
            amount_due=int(amount_due or 0),
            currency=str(getattr(invoice, "currency", "usd")),
            period_start=to_datetime(getattr(invoice, "period_start", None)),
            period_end=to_datetime(getattr(invoice, "period_end", None)),
            lines=lines,
        )


__all__ = ["StripeClient"]
