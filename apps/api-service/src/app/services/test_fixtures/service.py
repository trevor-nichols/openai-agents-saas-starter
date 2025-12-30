"""Deterministic seed orchestration for Playwright critical flows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.container import ApplicationContainer, get_container
from app.core.security import PASSWORD_HASH_VERSION, get_password_hash
from app.core.settings import get_settings
from app.domain.assets import AssetSourceTool, AssetType
from app.domain.platform_roles import PlatformRole
from app.domain.storage import StorageProviderLiteral
from app.domain.tenant_roles import TenantRole
from app.infrastructure.persistence.assets.models import AgentAsset
from app.infrastructure.persistence.auth.models.membership import TenantUserMembership
from app.infrastructure.persistence.auth.models.user import (
    PasswordHistory,
    UserAccount,
    UserProfile,
    UserStatus,
)
from app.infrastructure.persistence.billing.models import (
    BillingPlan,
    SubscriptionUsage,
    TenantSubscription,
)
from app.infrastructure.persistence.conversations.ids import coerce_conversation_uuid
from app.infrastructure.persistence.conversations.ledger_models import ConversationLedgerSegment
from app.infrastructure.persistence.conversations.models import AgentConversation, AgentMessage
from app.infrastructure.persistence.storage.models import StorageBucket, StorageObject
from app.infrastructure.persistence.tenants.models import TenantAccount
from app.infrastructure.persistence.usage.models import UsageCounter, UsageCounterGranularity
from app.infrastructure.storage.registry import get_storage_provider


class TestFixtureError(RuntimeError):
    """Raised when deterministic seed application fails."""


_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


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


class FixtureUsageCounter(BaseModel):
    period_start: date
    granularity: Literal["day", "month"] = "day"
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    requests: int = Field(default=0, ge=0)
    storage_bytes: int = Field(default=0, ge=0)
    user_email: EmailStr | None = None


class FixtureAsset(BaseModel):
    key: str = Field(min_length=1)
    asset_type: AssetType = Field(default="file")
    source_tool: AssetSourceTool | None = None
    filename: str = Field(min_length=1)
    mime_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    agent_key: str | None = Field(default=None, max_length=64)
    conversation_key: str | None = None
    message_id: int | None = Field(default=None, ge=1)
    tool_call_id: str | None = None
    response_id: str | None = None
    container_id: str | None = None
    openai_file_id: str | None = None
    user_email: EmailStr | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

class FixtureUser(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None
    role: TenantRole = Field(default=TenantRole.ADMIN)
    platform_role: PlatformRole | None = None
    verify_email: bool = True


class FixtureTenant(BaseModel):
    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    plan_code: str | None = None
    billing_email: EmailStr | None = None
    users: list[FixtureUser] = Field(default_factory=list)
    conversations: list[FixtureConversation] = Field(default_factory=list)
    usage: list[FixtureUsageEntry] = Field(default_factory=list)
    usage_counters: list[FixtureUsageCounter] = Field(default_factory=list)
    assets: list[FixtureAsset] = Field(default_factory=list)


class PlaywrightFixtureSpec(BaseModel):
    tenants: list[FixtureTenant] = Field(default_factory=list)


class FixtureUserResult(BaseModel):
    user_id: str
    role: TenantRole


class FixtureConversationResult(BaseModel):
    conversation_id: str
    status: str


class FixtureAssetResult(BaseModel):
    asset_id: str
    storage_object_id: str


class FixtureTenantResult(BaseModel):
    tenant_id: str
    plan_code: str | None
    users: dict[str, FixtureUserResult]
    conversations: dict[str, FixtureConversationResult]
    assets: dict[str, FixtureAssetResult] = Field(default_factory=dict)


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
    asset_results: dict[str, FixtureAssetResult]


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
                assets=context.asset_results,
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

                if tenant_spec.usage_counters:
                    await self._ensure_usage_counters(
                        session=session,
                        tenant=tenant,
                        user_results=user_results,
                        usage_counters=tenant_spec.usage_counters,
                    )

                asset_results: dict[str, FixtureAssetResult] = {}
                if tenant_spec.assets:
                    asset_results = await self._ensure_assets(
                        session=session,
                        tenant=tenant,
                        user_results=user_results,
                        conversation_results=conversation_results,
                        assets=tenant_spec.assets,
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
            asset_results=asset_results,
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
        # Explicit flush required because session autoflush is disabled; ensures FK targets exist.
        await session.flush()
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
                platform_role=user_spec.platform_role,
            )
            session.add(user)
        else:
            user.password_hash = hashed_password
            user.password_pepper_version = PASSWORD_HASH_VERSION
            user.status = UserStatus.ACTIVE
            user.platform_role = user_spec.platform_role
            if user_spec.verify_email:
                user.email_verified_at = now
            else:
                user.email_verified_at = None

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
            expected_id = coerce_conversation_uuid(convo.key)
            existing = await session.scalar(
                select(AgentConversation).where(
                    AgentConversation.tenant_id == tenant.id,
                    AgentConversation.conversation_key == convo.key,
                )
            )
            if existing is not None and existing.id != expected_id:
                await session.delete(existing)
                await session.flush()
                existing = None
            if existing is None:
                conversation = AgentConversation(
                    id=expected_id,
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

            # Ensure conversation row exists before inserting ledger segments.
            # Autoflush is disabled.
            await session.flush()

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

    async def _ensure_usage_counters(
        self,
        session: AsyncSession,
        tenant: TenantAccount,
        user_results: dict[str, FixtureUserResult],
        usage_counters: list[FixtureUsageCounter],
    ) -> None:
        now = datetime.now(UTC)
        for entry in usage_counters:
            user_id = (
                self._resolve_user_id(entry.user_email, user_results)
                if entry.user_email
                else None
            )
            granularity = UsageCounterGranularity(entry.granularity)
            stmt = select(UsageCounter).where(
                UsageCounter.tenant_id == tenant.id,
                UsageCounter.period_start == entry.period_start,
                UsageCounter.granularity == granularity,
            )
            if user_id is None:
                stmt = stmt.where(UsageCounter.user_id.is_(None))
            else:
                stmt = stmt.where(UsageCounter.user_id == user_id)

            existing = await session.scalar(stmt)
            if existing:
                existing.input_tokens = entry.input_tokens
                existing.output_tokens = entry.output_tokens
                existing.requests = entry.requests
                existing.storage_bytes = entry.storage_bytes
                existing.updated_at = now
            else:
                session.add(
                    UsageCounter(
                        id=uuid4(),
                        tenant_id=tenant.id,
                        user_id=user_id,
                        period_start=entry.period_start,
                        granularity=granularity,
                        input_tokens=entry.input_tokens,
                        output_tokens=entry.output_tokens,
                        requests=entry.requests,
                        storage_bytes=entry.storage_bytes,
                        created_at=now,
                        updated_at=now,
                    )
                )

    async def _ensure_assets(
        self,
        session: AsyncSession,
        tenant: TenantAccount,
        user_results: dict[str, FixtureUserResult],
        conversation_results: dict[str, FixtureConversationResult],
        assets: list[FixtureAsset],
    ) -> dict[str, FixtureAssetResult]:
        if not assets:
            return {}

        settings = get_settings()
        provider = get_storage_provider(settings)
        bucket_name = self._bucket_name(settings, tenant.id)
        region = self._bucket_region(settings)
        await provider.ensure_bucket(
            bucket_name,
            region=region,
            create_if_missing=self._should_auto_create_bucket(settings),
        )

        bucket = await session.scalar(
            select(StorageBucket).where(
                StorageBucket.tenant_id == tenant.id,
                StorageBucket.bucket_name == bucket_name,
            )
        )
        if bucket is None:
            bucket = StorageBucket(
                tenant_id=tenant.id,
                provider=settings.storage_provider.value,
                bucket_name=bucket_name,
                region=region,
                prefix=settings.storage_bucket_prefix,
                is_default=True,
                status="ready",
            )
            session.add(bucket)

        results: dict[str, FixtureAssetResult] = {}
        for asset in assets:
            if asset.key in results:
                raise TestFixtureError(f"Duplicate asset fixture key '{asset.key}'.")

            conversation_id = self._resolve_conversation_id(
                asset.conversation_key, conversation_results
            )
            user_id = (
                self._resolve_user_id(asset.user_email, user_results)
                if asset.user_email
                else None
            )

            storage_object_id = uuid5(
                NAMESPACE_URL, f"fixture-storage:{tenant.id}:{asset.key}"
            )
            asset_id = uuid5(NAMESPACE_URL, f"fixture-asset:{tenant.id}:{asset.key}")
            safe_filename = _safe_filename(asset.filename)
            object_key = f"{tenant.id}/{asset.key}/{safe_filename}"
            mime_type = asset.mime_type or "application/octet-stream"
            size_bytes = asset.size_bytes if asset.size_bytes is not None else 0

            storage_obj = await session.scalar(
                select(StorageObject).where(StorageObject.id == storage_object_id)
            )
            if storage_obj is None:
                storage_obj = StorageObject(
                    id=storage_object_id,
                    tenant_id=tenant.id,
                    bucket_id=bucket.id,
                    object_key=object_key,
                    filename=asset.filename,
                    mime_type=mime_type,
                    size_bytes=size_bytes,
                    checksum_sha256=None,
                    status="ready",
                    created_by_user_id=user_id,
                    agent_key=asset.agent_key,
                    conversation_id=conversation_id,
                    metadata_json=asset.metadata,
                    expires_at=None,
                )
                session.add(storage_obj)
            else:
                storage_obj.bucket_id = bucket.id
                storage_obj.object_key = object_key
                storage_obj.filename = asset.filename
                storage_obj.mime_type = mime_type
                storage_obj.size_bytes = size_bytes
                storage_obj.status = storage_obj.status or "ready"
                storage_obj.created_by_user_id = user_id
                storage_obj.agent_key = asset.agent_key
                storage_obj.conversation_id = conversation_id
                storage_obj.metadata_json = asset.metadata
                storage_obj.deleted_at = None

            asset_row = await session.scalar(
                select(AgentAsset).where(AgentAsset.id == asset_id)
            )
            if asset_row is None:
                asset_row = AgentAsset(
                    id=asset_id,
                    tenant_id=tenant.id,
                    storage_object_id=storage_object_id,
                    asset_type=asset.asset_type,
                    source_tool=asset.source_tool,
                    conversation_id=conversation_id,
                    message_id=asset.message_id,
                    tool_call_id=asset.tool_call_id,
                    response_id=asset.response_id,
                    container_id=asset.container_id,
                    openai_file_id=asset.openai_file_id,
                    metadata_json=asset.metadata,
                )
                session.add(asset_row)
            else:
                asset_row.storage_object_id = storage_object_id
                asset_row.asset_type = asset.asset_type
                asset_row.source_tool = asset.source_tool
                asset_row.conversation_id = conversation_id
                asset_row.message_id = asset.message_id
                asset_row.tool_call_id = asset.tool_call_id
                asset_row.response_id = asset.response_id
                asset_row.container_id = asset.container_id
                asset_row.openai_file_id = asset.openai_file_id
                asset_row.metadata_json = asset.metadata
                asset_row.deleted_at = None

            results[asset.key] = FixtureAssetResult(
                asset_id=str(asset_id),
                storage_object_id=str(storage_object_id),
            )

        return results

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

    @staticmethod
    def _resolve_conversation_id(
        key: str | None, conversation_results: dict[str, FixtureConversationResult]
    ) -> UUID | None:
        if key is None:
            return None
        entry = conversation_results.get(key)
        if entry is None:
            raise TestFixtureError(f"Asset references unknown conversation '{key}'.")
        return UUID(entry.conversation_id)

    @staticmethod
    def _bucket_name(settings, tenant_id: UUID) -> str:
        if settings.storage_provider == StorageProviderLiteral.GCS and settings.gcs_bucket:
            return settings.gcs_bucket
        if settings.storage_provider == StorageProviderLiteral.S3 and settings.s3_bucket:
            return settings.s3_bucket
        if (
            settings.storage_provider == StorageProviderLiteral.AZURE_BLOB
            and settings.azure_blob_container
        ):
            return settings.azure_blob_container
        prefix = settings.storage_bucket_prefix or "agent-data"
        tenant_token = str(tenant_id).replace("-", "")
        return f"{prefix}-{tenant_token}"

    @staticmethod
    def _bucket_region(settings) -> str | None:
        if settings.storage_provider == StorageProviderLiteral.MINIO:
            return settings.minio_region
        if settings.storage_provider == StorageProviderLiteral.S3:
            return settings.s3_region
        return None

    @staticmethod
    def _should_auto_create_bucket(settings) -> bool:
        return settings.storage_provider not in {
            StorageProviderLiteral.GCS,
            StorageProviderLiteral.S3,
            StorageProviderLiteral.AZURE_BLOB,
        }


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _safe_filename(filename: str) -> str:
    cleaned = _SAFE_CHARS.sub("-", filename).strip("-")
    return cleaned or "file"
__all__ = [
    "FixtureApplyResult",
    "PlaywrightFixtureSpec",
    "TestFixtureError",
    "TestFixtureService",
]
