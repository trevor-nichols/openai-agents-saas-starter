"""Deterministic seed orchestration for Playwright critical flows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, cast
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.container import ApplicationContainer, get_container
from app.core.security import PASSWORD_HASH_VERSION, get_password_hash
from app.infrastructure.persistence.auth.models import (
    PasswordHistory,
    TenantUserMembership,
    UserAccount,
    UserProfile,
    UserStatus,
)
from app.infrastructure.persistence.billing.models import (
    BillingPlan,
    SubscriptionUsage,
    TenantSubscription,
)
from app.infrastructure.persistence.conversations.ledger_models import ConversationLedgerSegment
from app.infrastructure.persistence.conversations.models import (
    AgentConversation,
    AgentMessage,
    TenantAccount,
)


class TestFixtureError(RuntimeError):
    """Raised when deterministic seed application fails."""


class FixtureConversationMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    text: str = Field(min_length=1)


class FixtureConversation(BaseModel):
    key: str = Field(min_length=1)
    agent_entrypoint: str = Field(default="default", min_length=1)
    status: Literal["active", "archived"] = "active"
    user_email: EmailStr | None = None
    messages: list[FixtureConversationMessage] = Field(default_factory=list)


class FixtureUsageEntry(BaseModel):
    feature_key: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit: str = Field(default="requests", min_length=1)
    period_start: datetime
    period_end: datetime | None = None
    idempotency_key: str | None = None

    @field_validator("period_end")
    @classmethod
    def _ensure_period_order(cls, value: datetime | None, info: ValidationInfo) -> datetime | None:
        if value is None:
            return None
        period_start = info.data.get("period_start")
        if not isinstance(period_start, datetime):
            return value
        if value < period_start:
            raise ValueError("period_end cannot be earlier than period_start")
        return value


class FixtureUser(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None
    role: str = Field(default="admin", min_length=3)
    verify_email: bool = True


class FixtureTenant(BaseModel):
    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    plan_code: str | None = None
    billing_email: EmailStr | None = None
    users: list[FixtureUser] = Field(default_factory=list)
    conversations: list[FixtureConversation] = Field(default_factory=list)
    usage: list[FixtureUsageEntry] = Field(default_factory=list)


class PlaywrightFixtureSpec(BaseModel):
    tenants: list[FixtureTenant] = Field(default_factory=list)


class FixtureUserResult(BaseModel):
    user_id: str
    role: str


class FixtureConversationResult(BaseModel):
    conversation_id: str
    status: str


class FixtureTenantResult(BaseModel):
    tenant_id: str
    plan_code: str | None
    users: dict[str, FixtureUserResult]
    conversations: dict[str, FixtureConversationResult]


class FixtureApplyResult(BaseModel):
    tenants: dict[str, FixtureTenantResult]
    generated_at: datetime


@dataclass(slots=True)
class _TenantContext:
    tenant: TenantAccount
    plan_code: str | None
    subscription: TenantSubscription | None
    user_results: dict[str, FixtureUserResult]
    conversation_results: dict[str, FixtureConversationResult]


class TestFixtureService:
    """Applies deterministic fixture specifications into the persistence layer."""

    def __init__(self, container: ApplicationContainer | None = None) -> None:
        self._container = container or get_container()

    async def apply_spec(self, spec: PlaywrightFixtureSpec) -> FixtureApplyResult:
        if not spec.tenants:
            raise TestFixtureError("Fixture specification must include at least one tenant.")

        session_factory = self._container.session_factory
        if session_factory is None:
            raise TestFixtureError("Database session factory is not configured.")

        results: dict[str, FixtureTenantResult] = {}
        for tenant_spec in spec.tenants:
            context = await self._apply_tenant(session_factory, tenant_spec)
            results[tenant_spec.slug] = FixtureTenantResult(
                tenant_id=str(context.tenant.id),
                plan_code=context.plan_code,
                users=context.user_results,
                conversations=context.conversation_results,
            )

        return FixtureApplyResult(tenants=results, generated_at=datetime.now(UTC))

    async def _apply_tenant(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        tenant_spec: FixtureTenant,
    ) -> _TenantContext:
        async with session_factory() as session:
            async with session.begin():
                tenant = await self._ensure_tenant(session, tenant_spec)
                subscription: TenantSubscription | None = None
                if tenant_spec.plan_code:
                    subscription = await self._ensure_subscription(
                        session=session,
                        tenant=tenant,
                        plan_code=tenant_spec.plan_code,
                        billing_email=tenant_spec.billing_email
                        or (tenant_spec.users[0].email if tenant_spec.users else None),
                    )

                user_results: dict[str, FixtureUserResult] = {}
                for user_spec in tenant_spec.users:
                    user_results[user_spec.email] = await self._ensure_user(
                        session=session,
                        tenant=tenant,
                        user_spec=user_spec,
                    )

                conversation_results: dict[str, FixtureConversationResult] = {}
                if tenant_spec.conversations:
                    conversation_results = await self._ensure_conversations(
                        session=session,
                        tenant=tenant,
                        user_results=user_results,
                        conversations=tenant_spec.conversations,
                    )

                if tenant_spec.usage and subscription is not None:
                    await self._ensure_usage_records(
                        session=session,
                        subscription=subscription,
                        usage_entries=tenant_spec.usage,
                    )

        return _TenantContext(
            tenant=tenant,
            plan_code=tenant_spec.plan_code,
            subscription=subscription,
            user_results=user_results,
            conversation_results=conversation_results,
        )

    async def _ensure_tenant(
        self,
        session: AsyncSession,
        tenant_spec: FixtureTenant,
    ) -> TenantAccount:
        existing = await session.scalar(
            select(TenantAccount).where(TenantAccount.slug == tenant_spec.slug)
        )
        if existing:
            existing.name = tenant_spec.name
            return existing

        tenant = TenantAccount(id=uuid4(), slug=tenant_spec.slug, name=tenant_spec.name)
        session.add(tenant)
        return tenant

    async def _ensure_user(
        self,
        session: AsyncSession,
        tenant: TenantAccount,
        user_spec: FixtureUser,
    ) -> FixtureUserResult:
        normalized_email = user_spec.email.lower()
        hashed_password = get_password_hash(user_spec.password)
        now = datetime.now(UTC)

        user = await session.scalar(
            select(UserAccount).where(UserAccount.email == normalized_email)
        )

        if user is None:
            user = UserAccount(
                id=uuid4(),
                email=normalized_email,
                password_hash=hashed_password,
                password_pepper_version=PASSWORD_HASH_VERSION,
                status=UserStatus.ACTIVE,
                email_verified_at=now if user_spec.verify_email else None,
            )
            session.add(user)
        else:
            user.password_hash = hashed_password
            user.password_pepper_version = PASSWORD_HASH_VERSION
            user.status = UserStatus.ACTIVE
            if user_spec.verify_email:
                user.email_verified_at = now

        profile = await session.scalar(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        if user_spec.display_name:
            if profile:
                profile.display_name = user_spec.display_name
            else:
                session.add(
                    UserProfile(
                        id=uuid4(),
                        user_id=user.id,
                        display_name=user_spec.display_name,
                    )
                )

        membership = await session.scalar(
            select(TenantUserMembership).where(
                TenantUserMembership.user_id == user.id,
                TenantUserMembership.tenant_id == tenant.id,
            )
        )
        if membership:
            membership.role = user_spec.role
        else:
            membership = TenantUserMembership(
                id=uuid4(),
                user_id=user.id,
                tenant_id=tenant.id,
                role=user_spec.role,
            )
            session.add(membership)

        existing_history = await session.scalar(
            select(PasswordHistory).where(
                PasswordHistory.user_id == user.id,
                PasswordHistory.password_hash == hashed_password,
            )
        )
        if existing_history is None:
            session.add(
                PasswordHistory(
                    id=uuid4(),
                    user_id=user.id,
                    password_hash=hashed_password,
                    password_pepper_version=PASSWORD_HASH_VERSION,
                    created_at=now,
                )
            )

        return FixtureUserResult(user_id=str(user.id), role=membership.role)

    async def _ensure_subscription(
        self,
        session: AsyncSession,
        tenant: TenantAccount,
        *,
        plan_code: str,
        billing_email: str | None,
    ) -> TenantSubscription:
        plan = await session.scalar(select(BillingPlan).where(BillingPlan.code == plan_code))
        if plan is None:
            raise TestFixtureError(f"Billing plan '{plan_code}' not found.")

        subscription = await session.scalar(
            select(TenantSubscription).where(TenantSubscription.tenant_id == tenant.id)
        )

        now = datetime.now(UTC)
        next_month = now + timedelta(days=30)
        metadata = {"seeded_by": "test_fixture_service"}
        if subscription is None:
            subscription = TenantSubscription(
                id=uuid4(),
                tenant_id=tenant.id,
                plan_id=plan.id,
                status="active",
                auto_renew=True,
                billing_email=billing_email,
                processor="fixture",
                processor_customer_id=f"fixture-{tenant.id}",
                processor_subscription_id=f"fixture-sub-{tenant.id}",
                starts_at=now,
                current_period_start=now,
                current_period_end=next_month,
                seat_count=plan.seat_included or 1,
                metadata_json=metadata,
            )
            session.add(subscription)
        else:
            subscription.plan_id = plan.id
            subscription.status = "active"
            subscription.auto_renew = True
            subscription.billing_email = billing_email
            subscription.processor = subscription.processor or "fixture"
            subscription.processor_customer_id = (
                subscription.processor_customer_id or f"fixture-{tenant.id}"
            )
            subscription.processor_subscription_id = (
                subscription.processor_subscription_id or f"fixture-sub-{tenant.id}"
            )
            subscription.current_period_start = subscription.current_period_start or now
            subscription.current_period_end = subscription.current_period_end or next_month
            metadata_payload = subscription.metadata_json or {}
            metadata_payload.update(metadata)
            subscription.metadata_json = metadata_payload

        return subscription

    async def _ensure_conversations(
        self,
        session: AsyncSession,
        tenant: TenantAccount,
        user_results: dict[str, FixtureUserResult],
        conversations: list[FixtureConversation],
    ) -> dict[str, FixtureConversationResult]:
        results: dict[str, FixtureConversationResult] = {}
        now = datetime.now(UTC)
        for convo in conversations:
            existing = await session.scalar(
                select(AgentConversation).where(
                    AgentConversation.tenant_id == tenant.id,
                    AgentConversation.conversation_key == convo.key,
                )
            )
            if existing is None:
                conversation = AgentConversation(
                    id=uuid4(),
                    conversation_key=convo.key,
                    tenant_id=tenant.id,
                    user_id=self._resolve_user_id(convo.user_email, user_results),
                    agent_entrypoint=convo.agent_entrypoint,
                    status=convo.status,
                    created_at=now,
                    updated_at=now,
                    last_message_at=now if convo.messages else None,
                )
                session.add(conversation)
            else:
                conversation = existing
                conversation.agent_entrypoint = convo.agent_entrypoint
                conversation.status = convo.status
                conversation.user_id = self._resolve_user_id(convo.user_email, user_results)
                conversation.updated_at = now
                conversation.last_message_at = (
                    now if convo.messages else conversation.last_message_at
                )

            await session.execute(
                delete(AgentMessage).where(AgentMessage.conversation_id == conversation.id)
            )
            await session.execute(
                delete(ConversationLedgerSegment).where(
                    ConversationLedgerSegment.conversation_id == conversation.id
                )
            )

            segment_id = uuid4()
            session.add(
                ConversationLedgerSegment(
                    id=segment_id,
                    tenant_id=tenant.id,
                    conversation_id=conversation.id,
                    segment_index=0,
                    created_at=now,
                    updated_at=now,
                )
            )

            for index, message in enumerate(convo.messages):
                random_bits = cast(int, uuid4().int)
                message_id = random_bits & ((1 << 63) - 1)
                session.add(
                    AgentMessage(
                        id=message_id,
                        conversation_id=conversation.id,
                        segment_id=segment_id,
                        position=index,
                        role=message.role,
                        content={"type": "text", "text": message.text},
                    )
                )

            conversation.message_count = len(convo.messages)
            conversation.total_tokens_prompt = 0
            conversation.total_tokens_completion = 0

            results[convo.key] = FixtureConversationResult(
                conversation_id=str(conversation.id),
                status=conversation.status,
            )
        return results

    async def _ensure_usage_records(
        self,
        session: AsyncSession,
        subscription: TenantSubscription,
        usage_entries: list[FixtureUsageEntry],
    ) -> None:
        for entry in usage_entries:
            period_start = _ensure_utc(entry.period_start)
            period_end = _ensure_utc(entry.period_end or (period_start + timedelta(days=1)))

            existing = await session.scalar(
                select(SubscriptionUsage).where(
                    SubscriptionUsage.subscription_id == subscription.id,
                    SubscriptionUsage.feature_key == entry.feature_key,
                    SubscriptionUsage.period_start == period_start,
                )
            )

            if existing:
                existing.quantity = entry.quantity
                existing.period_end = period_end
                existing.unit = entry.unit
                existing.external_event_id = entry.idempotency_key or existing.external_event_id
            else:
                session.add(
                    SubscriptionUsage(
                        id=uuid4(),
                        subscription_id=subscription.id,
                        feature_key=entry.feature_key,
                        unit=entry.unit,
                        period_start=period_start,
                        period_end=period_end,
                        quantity=entry.quantity,
                        external_event_id=entry.idempotency_key,
                    )
                )

    @staticmethod
    def _resolve_user_id(
        email: str | None, user_results: dict[str, FixtureUserResult]
    ) -> UUID | None:
        if email is None:
            return None
        entry = user_results.get(email)
        if entry is None:
            raise TestFixtureError(f"Conversation references unknown user '{email}'.")
        return UUID(entry.user_id)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
__all__ = [
    "FixtureApplyResult",
    "PlaywrightFixtureSpec",
    "TestFixtureError",
    "TestFixtureService",
]
