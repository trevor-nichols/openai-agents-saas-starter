"""Postgres-backed billing repository implementation."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.domain.billing import (
    BillingCustomerRecord,
    BillingPlan,
    BillingRepository,
    PlanFeature,
    SubscriptionInvoiceRecord,
    TenantSubscription,
    UsageTotal,
)
from app.infrastructure.persistence.billing.models import (
    BillingCustomer as ORMBillingCustomer,
)
from app.infrastructure.persistence.billing.models import (
    BillingPlan as ORMPlan,
)
from app.infrastructure.persistence.billing.models import (
    PlanFeature as ORMPlanFeature,
)
from app.infrastructure.persistence.billing.models import (
    SubscriptionInvoice as ORMSubscriptionInvoice,
)
from app.infrastructure.persistence.billing.models import (
    SubscriptionUsage as ORMSubscriptionUsage,
)
from app.infrastructure.persistence.billing.models import (
    TenantSubscription as ORMTenantSubscription,
)

logger = logging.getLogger("api-service.persistence.billing")


class PostgresBillingRepository(BillingRepository):
    """Persist and fetch billing data using SQLAlchemy models."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_plans(self) -> list[BillingPlan]:
        async with self._session_factory() as session:
            result = await session.execute(select(ORMPlan).options(selectinload(ORMPlan.features)))
            plans = [self._to_domain_plan(row) for row in result.scalars()]
            logger.debug("Fetched %s billing plans from Postgres.", len(plans))
            return plans

    async def get_subscription(self, tenant_id: str) -> TenantSubscription | None:
        async with self._session_factory() as session:
            tenant_uuid = self._parse_tenant_uuid(tenant_id)
            result = await session.execute(
                select(ORMTenantSubscription)
                .options(selectinload(ORMTenantSubscription.plan))
                .where(ORMTenantSubscription.tenant_id == tenant_uuid)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return self._to_domain_subscription(row)

    async def upsert_subscription(self, subscription: TenantSubscription) -> None:
        async with self._session_factory() as session:
            plan_row = await session.scalar(
                select(ORMPlan).where(ORMPlan.code == subscription.plan_code)
            )
            if plan_row is None:
                raise ValueError(f"Billing plan '{subscription.plan_code}' not found.")

            tenant_uuid = self._parse_tenant_uuid(subscription.tenant_id)
            existing = await session.scalar(
                select(ORMTenantSubscription).where(ORMTenantSubscription.tenant_id == tenant_uuid)
            )

            if existing is None:
                entity = ORMTenantSubscription(
                    id=uuid.uuid4(),
                    tenant_id=tenant_uuid,
                    plan_id=plan_row.id,
                    status=subscription.status,
                    auto_renew=subscription.auto_renew,
                    billing_email=subscription.billing_email,
                    processor=subscription.processor,
                    processor_customer_id=subscription.processor_customer_id,
                    processor_subscription_id=subscription.processor_subscription_id,
                    starts_at=subscription.starts_at,
                    current_period_start=subscription.current_period_start,
                    current_period_end=subscription.current_period_end,
                    trial_ends_at=subscription.trial_ends_at,
                    cancel_at=subscription.cancel_at,
                    seat_count=subscription.seat_count,
                    metadata_json=_serialize_subscription_metadata(subscription),
                )
                session.add(entity)
            else:
                existing.plan_id = plan_row.id
                existing.status = subscription.status
                existing.auto_renew = subscription.auto_renew
                existing.billing_email = subscription.billing_email
                existing.processor = subscription.processor
                existing.processor_customer_id = subscription.processor_customer_id
                existing.processor_subscription_id = subscription.processor_subscription_id
                existing.starts_at = subscription.starts_at
                existing.current_period_start = subscription.current_period_start
                existing.current_period_end = subscription.current_period_end
                existing.trial_ends_at = subscription.trial_ends_at
                existing.cancel_at = subscription.cancel_at
                existing.seat_count = subscription.seat_count
                existing.metadata_json = _serialize_subscription_metadata(subscription)
                existing.updated_at = datetime.now(UTC)

            await session.commit()

    async def update_subscription(
        self,
        tenant_id: str,
        *,
        auto_renew: bool | None = None,
        billing_email: str | None = None,
        seat_count: int | None = None,
    ) -> TenantSubscription:
        async with self._session_factory() as session:
            tenant_uuid = self._parse_tenant_uuid(tenant_id)
            subscription = await session.scalar(
                select(ORMTenantSubscription)
                .options(selectinload(ORMTenantSubscription.plan))
                .where(ORMTenantSubscription.tenant_id == tenant_uuid)
            )
            if subscription is None:
                raise ValueError(f"Tenant '{tenant_id}' does not have a subscription.")

            if auto_renew is not None:
                subscription.auto_renew = auto_renew
            if billing_email is not None:
                subscription.billing_email = billing_email
            if seat_count is not None:
                subscription.seat_count = seat_count

            subscription.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(subscription)
            return self._to_domain_subscription(subscription)

    async def get_customer(
        self, tenant_id: str, *, processor: str
    ) -> BillingCustomerRecord | None:
        async with self._session_factory() as session:
            tenant_uuid = self._parse_tenant_uuid(tenant_id)
            result = await session.execute(
                select(ORMBillingCustomer).where(
                    ORMBillingCustomer.tenant_id == tenant_uuid,
                    ORMBillingCustomer.processor == processor,
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return self._to_domain_customer(row)

    async def upsert_customer(
        self, customer: BillingCustomerRecord
    ) -> BillingCustomerRecord:
        async with self._session_factory() as session:
            tenant_uuid = self._parse_tenant_uuid(customer.tenant_id)
            existing = await session.scalar(
                select(ORMBillingCustomer).where(
                    ORMBillingCustomer.tenant_id == tenant_uuid,
                    ORMBillingCustomer.processor == customer.processor,
                )
            )
            if existing is None:
                entity = ORMBillingCustomer(
                    id=uuid.uuid4(),
                    tenant_id=tenant_uuid,
                    processor=customer.processor,
                    processor_customer_id=customer.processor_customer_id,
                    billing_email=customer.billing_email,
                )
                session.add(entity)
                await session.commit()
                await session.refresh(entity)
                return self._to_domain_customer(entity)

            existing.processor_customer_id = customer.processor_customer_id
            existing.billing_email = customer.billing_email
            existing.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(existing)
            return self._to_domain_customer(existing)

    async def record_usage(
        self,
        tenant_id: str,
        *,
        feature_key: str,
        quantity: int,
        period_start: datetime,
        period_end: datetime,
        idempotency_key: str | None = None,
    ) -> None:
        async with self._session_factory() as session:
            subscription = await self._get_subscription_row(session, tenant_id)
            if subscription is None:
                raise ValueError(f"Tenant '{tenant_id}' does not have a subscription.")

            await self._insert_usage_record(
                session,
                subscription_id=subscription.id,
                feature_key=feature_key,
                quantity=quantity,
                period_start=period_start,
                period_end=period_end,
                idempotency_key=idempotency_key,
            )
            await session.commit()

    async def record_usage_from_processor(
        self,
        tenant_id: str,
        *,
        feature_key: str,
        quantity: int,
        period_start: datetime,
        period_end: datetime,
        idempotency_key: str | None = None,
    ) -> None:
        async with self._session_factory() as session:
            subscription = await self._get_subscription_row(session, tenant_id)
            if subscription is None:
                raise ValueError(f"Tenant '{tenant_id}' does not have a subscription.")

            await self._insert_usage_record(
                session,
                subscription_id=subscription.id,
                feature_key=feature_key,
                quantity=quantity,
                period_start=period_start,
                period_end=period_end,
                idempotency_key=idempotency_key,
            )
            await session.commit()

    async def get_usage_totals(
        self,
        tenant_id: str,
        *,
        feature_keys: Sequence[str] | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> list[UsageTotal]:
        async with self._session_factory() as session:
            tenant_uuid = self._parse_tenant_uuid(tenant_id)
            query = (
                select(
                    ORMSubscriptionUsage.feature_key,
                    func.sum(ORMSubscriptionUsage.quantity).label("total_quantity"),
                    func.min(ORMSubscriptionUsage.period_start).label("min_period_start"),
                    func.max(ORMSubscriptionUsage.period_end).label("max_period_end"),
                    func.min(ORMSubscriptionUsage.unit).label("unit"),
                )
                .join(
                    ORMTenantSubscription,
                    ORMSubscriptionUsage.subscription_id == ORMTenantSubscription.id,
                )
                .where(ORMTenantSubscription.tenant_id == tenant_uuid)
            )

            if feature_keys:
                query = query.where(ORMSubscriptionUsage.feature_key.in_(feature_keys))
            if period_start:
                query = query.where(ORMSubscriptionUsage.period_end >= period_start)
            if period_end:
                query = query.where(ORMSubscriptionUsage.period_start <= period_end)

            query = query.group_by(ORMSubscriptionUsage.feature_key)
            result = await session.execute(query)
            rows = result.all()

        usage_totals: list[UsageTotal] = []
        for row in rows:
            if row.total_quantity is None:
                continue
            window_start = period_start or row.min_period_start
            window_end = period_end or row.max_period_end
            usage_totals.append(
                UsageTotal(
                    feature_key=row.feature_key,
                    unit=row.unit or "units",
                    quantity=int(row.total_quantity),
                    window_start=window_start,
                    window_end=window_end,
                )
            )
        return usage_totals

    async def upsert_invoice(self, invoice: SubscriptionInvoiceRecord) -> None:
        async with self._session_factory() as session:
            subscription = await self._get_subscription_row(session, invoice.tenant_id)
            if subscription is None:
                raise ValueError(f"Tenant '{invoice.tenant_id}' does not have a subscription.")

            existing = None
            if invoice.processor_invoice_id:
                existing = await session.scalar(
                    select(ORMSubscriptionInvoice)
                    .where(ORMSubscriptionInvoice.subscription_id == subscription.id)
                    .where(
                        ORMSubscriptionInvoice.external_invoice_id == invoice.processor_invoice_id
                    )
                )
            if existing is None:
                existing = await session.scalar(
                    select(ORMSubscriptionInvoice)
                    .where(ORMSubscriptionInvoice.subscription_id == subscription.id)
                    .where(ORMSubscriptionInvoice.period_start == invoice.period_start)
                )

            if existing is None:
                entity = ORMSubscriptionInvoice(
                    id=uuid.uuid4(),
                    subscription_id=subscription.id,
                    period_start=invoice.period_start,
                    period_end=invoice.period_end,
                    amount_cents=invoice.amount_cents,
                    currency=invoice.currency,
                    status=invoice.status,
                    external_invoice_id=invoice.processor_invoice_id,
                    hosted_invoice_url=invoice.hosted_invoice_url,
                )
                session.add(entity)
            else:
                existing.period_start = invoice.period_start
                existing.period_end = invoice.period_end
                existing.amount_cents = invoice.amount_cents
                existing.currency = invoice.currency
                existing.status = invoice.status
                existing.external_invoice_id = invoice.processor_invoice_id
                existing.hosted_invoice_url = invoice.hosted_invoice_url

            await session.commit()

    async def _get_subscription_row(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> ORMTenantSubscription | None:
        tenant_uuid = self._parse_tenant_uuid(tenant_id)
        return await session.scalar(
            select(ORMTenantSubscription).where(ORMTenantSubscription.tenant_id == tenant_uuid)
        )

    async def _insert_usage_record(
        self,
        session: AsyncSession,
        *,
        subscription_id: uuid.UUID,
        feature_key: str,
        quantity: int,
        period_start: datetime,
        period_end: datetime,
        idempotency_key: str | None,
    ) -> None:
        if idempotency_key:
            existing = await session.scalar(
                select(ORMSubscriptionUsage).where(
                    ORMSubscriptionUsage.subscription_id == subscription_id,
                    ORMSubscriptionUsage.feature_key == feature_key,
                    ORMSubscriptionUsage.external_event_id == idempotency_key,
                )
            )
            if existing is not None:
                return

        usage = ORMSubscriptionUsage(
            id=uuid.uuid4(),
            subscription_id=subscription_id,
            feature_key=feature_key,
            unit="units",
            period_start=period_start,
            period_end=period_end,
            quantity=quantity,
            reported_at=datetime.now(UTC),
            external_event_id=idempotency_key,
        )
        session.add(usage)

    @staticmethod
    def _to_domain_plan(plan: ORMPlan) -> BillingPlan:
        return BillingPlan(
            code=plan.code,
            name=plan.name,
            interval=plan.interval,
            interval_count=plan.interval_count,
            price_cents=plan.price_cents,
            currency=plan.currency,
            trial_days=plan.trial_days,
            seat_included=plan.seat_included,
            feature_toggles=plan.feature_toggles or {},
            features=[
                PostgresBillingRepository._to_domain_feature(feature) for feature in plan.features
            ],
            is_active=plan.is_active,
        )

    @staticmethod
    def _to_domain_feature(feature: ORMPlanFeature) -> PlanFeature:
        return PlanFeature(
            key=feature.feature_key,
            display_name=feature.display_name or feature.feature_key,
            description=feature.description,
            hard_limit=feature.hard_limit,
            soft_limit=feature.soft_limit,
            is_metered=feature.is_metered,
        )

    @staticmethod
    def _to_domain_subscription(subscription: ORMTenantSubscription) -> TenantSubscription:
        metadata_payload = dict(subscription.metadata_json or {})
        pending_plan_code = metadata_payload.pop("pending_plan_code", None)
        if pending_plan_code == "":
            pending_plan_code = None
        pending_plan_effective_at = _parse_metadata_datetime(
            metadata_payload.pop("pending_plan_effective_at", None)
        )
        pending_seat_count = metadata_payload.pop("pending_seat_count", None)
        processor_schedule_id = metadata_payload.pop("processor_schedule_id", None)
        if processor_schedule_id == "":
            processor_schedule_id = None

        return TenantSubscription(
            tenant_id=str(subscription.tenant_id),
            plan_code=_safe_plan_code(subscription),
            status=subscription.status,
            auto_renew=subscription.auto_renew,
            billing_email=subscription.billing_email,
            starts_at=subscription.starts_at,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            trial_ends_at=subscription.trial_ends_at,
            cancel_at=subscription.cancel_at,
            seat_count=subscription.seat_count,
            pending_plan_code=pending_plan_code,
            pending_plan_effective_at=pending_plan_effective_at,
            pending_seat_count=_coerce_int(pending_seat_count),
            metadata=metadata_payload,
            processor=subscription.processor,
            processor_customer_id=subscription.processor_customer_id,
            processor_subscription_id=subscription.processor_subscription_id,
            processor_schedule_id=processor_schedule_id,
        )

    @staticmethod
    def _to_domain_customer(customer: ORMBillingCustomer) -> BillingCustomerRecord:
        return BillingCustomerRecord(
            tenant_id=str(customer.tenant_id),
            processor=customer.processor,
            processor_customer_id=customer.processor_customer_id,
            billing_email=customer.billing_email,
        )

    @staticmethod
    def _parse_tenant_uuid(tenant_id: str) -> uuid.UUID:
        try:
            return uuid.UUID(str(tenant_id))
        except (ValueError, TypeError) as exc:
            raise ValueError("Tenant identifier must be a valid UUID.") from exc


def _safe_plan_code(subscription: ORMTenantSubscription) -> str:
    if subscription.plan:
        return subscription.plan.code
    return str(subscription.plan_id)


def _serialize_subscription_metadata(subscription: TenantSubscription) -> dict[str, object]:
    metadata: dict[str, object] = dict(subscription.metadata or {})
    _set_metadata_value(metadata, "processor_schedule_id", subscription.processor_schedule_id)
    _set_metadata_value(metadata, "pending_plan_code", subscription.pending_plan_code)
    _set_metadata_value(
        metadata,
        "pending_plan_effective_at",
        _format_metadata_datetime(subscription.pending_plan_effective_at),
    )
    _set_metadata_value(metadata, "pending_seat_count", subscription.pending_seat_count)
    return metadata


def _set_metadata_value(metadata: dict[str, object], key: str, value: object | None) -> None:
    if value is None or value == "":
        metadata.pop(key, None)
        return
    metadata[key] = value


def _format_metadata_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _parse_metadata_datetime(value: object | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _coerce_int(value: object | None) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float, str)):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return None
