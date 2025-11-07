"""Typed Stripe client wrappers with retries and error translation."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

import stripe

from app.observability.metrics import observe_stripe_api_call

logger = logging.getLogger("anything-agents.infrastructure.stripe")


@dataclass(slots=True)
class StripeCustomer:
    id: str
    email: str | None = None


@dataclass(slots=True)
class StripeSubscriptionItem:
    id: str
    price_id: str | None
    quantity: int | None


@dataclass(slots=True)
class StripeSubscription:
    id: str
    customer_id: str
    status: str
    cancel_at_period_end: bool
    current_period_start: datetime | None
    current_period_end: datetime | None
    trial_end: datetime | None
    items: list[StripeSubscriptionItem]

    @property
    def primary_item(self) -> StripeSubscriptionItem | None:
        return self.items[0] if self.items else None


@dataclass(slots=True)
class StripeUsageRecord:
    id: str
    subscription_item_id: str
    quantity: int
    timestamp: datetime


class StripeClientError(RuntimeError):
    """Wrapper for unrecoverable Stripe API failures."""

    def __init__(self, operation: str, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.operation = operation
        self.code = code


class StripeClient:
    """Lightweight async-friendly Stripe wrapper with retries and metrics."""

    RETRYABLE_ERRORS = (
        stripe.error.APIConnectionError,
        stripe.error.APIError,
        stripe.error.RateLimitError,
        stripe.error.IdempotencyError,
    )

    def __init__(
        self,
        api_key: str,
        *,
        max_attempts: int = 3,
        initial_backoff_seconds: float = 0.5,
    ) -> None:
        if not api_key:
            raise StripeClientError("config", "Stripe secret key is required.")
        self._api_key = api_key
        self._max_attempts = max(1, max_attempts)
        self._initial_backoff = max(0.1, initial_backoff_seconds)
        stripe.api_key = api_key
        stripe.max_network_retries = 0  # rely on our own retry logic

    async def create_customer(self, *, email: str | None, tenant_id: str) -> StripeCustomer:
        payload: dict[str, Any] = {
            "metadata": {"tenant_id": tenant_id},
            "description": f"Tenant {tenant_id}",
        }
        if email:
            payload["email"] = email

        customer = await self._request(
            "customer.create",
            lambda: stripe.Customer.create(**payload),
        )
        return StripeCustomer(id=customer.id, email=customer.email)

    async def create_subscription(
        self,
        *,
        customer_id: str,
        price_id: str,
        quantity: int,
        auto_renew: bool,
        metadata: dict[str, str] | None = None,
    ) -> StripeSubscription:
        params: dict[str, Any] = {
            "customer": customer_id,
            "items": [
                {
                    "price": price_id,
                    "quantity": quantity,
                }
            ],
            "metadata": metadata or {},
            "expand": ["items.data.price"],
        }
        if not auto_renew:
            params["cancel_at_period_end"] = True

        subscription = await self._request(
            "subscription.create",
            lambda: stripe.Subscription.create(**params),
        )
        return self._to_subscription(subscription)

    async def retrieve_subscription(self, subscription_id: str) -> StripeSubscription:
        subscription = await self._request(
            "subscription.retrieve",
            lambda: stripe.Subscription.retrieve(subscription_id, expand=["items.data.price"]),
        )
        return self._to_subscription(subscription)

    async def modify_subscription(
        self,
        subscription: StripeSubscription,
        *,
        auto_renew: bool | None = None,
        seat_count: int | None = None,
    ) -> StripeSubscription:
        params: dict[str, Any] = {"expand": ["items.data.price"]}
        if auto_renew is not None:
            params["cancel_at_period_end"] = not auto_renew
        if seat_count is not None:
            item = subscription.primary_item
            if item is None:
                raise StripeClientError("subscription.modify", "Subscription has no items to update quantity.")
            params.setdefault("items", [])
            params["items"].append({"id": item.id, "quantity": seat_count})

        if len(params) == 1:  # only expand present
            return subscription

        updated = await self._request(
            "subscription.modify",
            lambda: stripe.Subscription.modify(subscription.id, **params),
        )
        return self._to_subscription(updated)

    async def cancel_subscription(self, subscription_id: str, *, cancel_at_period_end: bool) -> StripeSubscription:
        params: dict[str, Any] = {
            "expand": ["items.data.price"],
        }
        cancel_fn: Callable[[], Any]
        if cancel_at_period_end:
            cancel_fn = lambda: stripe.Subscription.modify(subscription_id, cancel_at_period_end=True, **params)
        else:
            cancel_fn = lambda: stripe.Subscription.delete(subscription_id, **params)

        subscription = await self._request("subscription.cancel", cancel_fn)
        return self._to_subscription(subscription)

    async def update_customer_email(self, customer_id: str, email: str) -> StripeCustomer:
        customer = await self._request(
            "customer.modify",
            lambda: stripe.Customer.modify(customer_id, email=email),
        )
        return StripeCustomer(id=customer.id, email=customer.email)

    async def create_usage_record(
        self,
        subscription_item_id: str,
        *,
        quantity: int,
        timestamp: int,
        idempotency_key: str,
        feature_key: str,
    ) -> StripeUsageRecord:
        record = await self._request(
            "usage_record.create",
            lambda: stripe.SubscriptionItem.create_usage_record(
                subscription_item_id,
                quantity=quantity,
                timestamp=timestamp,
                action="increment",
                idempotency_key=idempotency_key,
                metadata={"feature": feature_key},
            ),
        )
        ts = _to_datetime(record.timestamp)
        return StripeUsageRecord(
            id=record.id,
            subscription_item_id=record.subscription_item,
            quantity=record.quantity,
            timestamp=ts or datetime.now(timezone.utc),
        )

    async def _request(self, operation: str, func: Callable[[], Any]) -> Any:
        attempt = 0
        last_error: Exception | None = None
        while attempt < self._max_attempts:
            attempt += 1
            start = time.perf_counter()
            try:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, func)
                observe_stripe_api_call(operation=operation, result="success", duration_seconds=time.perf_counter() - start)
                return result
            except stripe.error.StripeError as exc:  # type: ignore[misc]
                observe_stripe_api_call(
                    operation=operation,
                    result=_stripe_error_code(exc),
                    duration_seconds=time.perf_counter() - start,
                )
                logger.warning(
                    "Stripe API error on %s (attempt %s/%s): %s",
                    operation,
                    attempt,
                    self._max_attempts,
                    exc.user_message or str(exc),
                )
                if attempt >= self._max_attempts or not self._should_retry(exc):
                    raise StripeClientError(operation, exc.user_message or str(exc), code=_stripe_error_code(exc)) from exc
                await asyncio.sleep(self._backoff(attempt))
                last_error = exc
            except Exception as exc:  # pragma: no cover - unexpected runtime failure
                observe_stripe_api_call(
                    operation=operation,
                    result="exception",
                    duration_seconds=time.perf_counter() - start,
                )
                logger.exception("Unexpected error during Stripe operation %s", operation)
                raise StripeClientError(operation, str(exc)) from exc
        raise StripeClientError(operation, str(last_error or "Unknown Stripe error"))

    def _backoff(self, attempt: int) -> float:
        jitter = random.uniform(0, self._initial_backoff)
        return self._initial_backoff * (2 ** (attempt - 1)) + jitter

    def _should_retry(self, exc: stripe.error.StripeError) -> bool:
        return isinstance(exc, self.RETRYABLE_ERRORS)

    def _to_subscription(self, subscription: Any) -> StripeSubscription:
        items = [self._to_subscription_item(item) for item in _iter_items(subscription.items)]
        return StripeSubscription(
            id=subscription.id,
            customer_id=subscription.customer,
            status=subscription.status,
            cancel_at_period_end=bool(subscription.cancel_at_period_end),
            current_period_start=_to_datetime(getattr(subscription, "current_period_start", None)),
            current_period_end=_to_datetime(getattr(subscription, "current_period_end", None)),
            trial_end=_to_datetime(getattr(subscription, "trial_end", None)),
            items=items,
        )

    def _to_subscription_item(self, item: Any) -> StripeSubscriptionItem:
        price = getattr(item, "price", None)
        price_id = getattr(price, "id", None) if price else None
        return StripeSubscriptionItem(
            id=item.id,
            price_id=price_id,
            quantity=getattr(item, "quantity", None),
        )


def _iter_items(items: Any) -> Iterable[Any]:
    data = getattr(items, "data", None)
    if isinstance(data, list):
        return data
    return []


def _stripe_error_code(exc: stripe.error.StripeError) -> str:
    code = getattr(exc, "code", None)
    if code:
        return str(code)
    return exc.error.type if getattr(exc, "error", None) else exc.__class__.__name__


def _to_datetime(value: int | float | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(float(value), tz=timezone.utc)
