"""Postgres repository for status subscriptions."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import desc, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.status import (
    StatusSubscription,
    StatusSubscriptionCreate,
    StatusSubscriptionListResult,
    StatusSubscriptionRepository,
)
from app.infrastructure.persistence.status.models import StatusSubscriptionModel
from app.infrastructure.security.cipher import build_cipher, decrypt_optional, encrypt_optional


class PostgresStatusSubscriptionRepository(StatusSubscriptionRepository):
    """Persist status subscriptions in Postgres."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        encryption_secret: str,
    ) -> None:
        self._session_factory = session_factory
        self._cipher = build_cipher(encryption_secret)
        if self._cipher is None:
            raise ValueError("Status subscription encryption secret is required.")

    async def create(self, payload: StatusSubscriptionCreate) -> StatusSubscription:
        record = StatusSubscriptionModel(
            channel=payload.channel,
            target_hash=payload.target_hash,
            target_masked=payload.target_masked,
            target_encrypted=self._ensure_encrypt(payload.target),
            severity_filter=payload.severity_filter,
            status=payload.status,
            metadata_json=dict(payload.metadata),
            tenant_id=payload.tenant_id,
            created_by=payload.created_by,
            verification_token_hash=payload.verification_token_hash,
            verification_expires_at=payload.verification_expires_at,
            challenge_token_hash=payload.challenge_token_hash,
            webhook_secret_encrypted=self._ensure_encrypt(payload.webhook_secret),
            unsubscribe_token_hash=payload.unsubscribe_token_hash,
            unsubscribe_token_encrypted=self._ensure_encrypt(payload.unsubscribe_token),
        )
        async with self._session_factory() as session:
            session.add(record)
            await session.commit()
            await session.refresh(record)
        return self._to_domain(record)

    async def find_by_id(self, subscription_id: uuid.UUID) -> StatusSubscription | None:
        async with self._session_factory() as session:
            record = await session.get(StatusSubscriptionModel, subscription_id)
        return self._to_domain(record) if record else None

    async def find_by_verification_hash(
        self, token_hash: str
    ) -> StatusSubscription | None:
        stmt = select(StatusSubscriptionModel).where(
            StatusSubscriptionModel.verification_token_hash == token_hash
        )
        async with self._session_factory() as session:
            record = (await session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(record) if record else None

    async def find_by_challenge_hash(
        self, token_hash: str
    ) -> StatusSubscription | None:
        stmt = select(StatusSubscriptionModel).where(
            StatusSubscriptionModel.challenge_token_hash == token_hash
        )
        async with self._session_factory() as session:
            record = (await session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(record) if record else None

    async def find_by_unsubscribe_hash(
        self, token_hash: str
    ) -> StatusSubscription | None:
        stmt = select(StatusSubscriptionModel).where(
            StatusSubscriptionModel.unsubscribe_token_hash == token_hash
        )
        async with self._session_factory() as session:
            record = (await session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(record) if record else None

    async def list_subscriptions(
        self,
        *,
        tenant_id: uuid.UUID | None,
        status: str | None,
        limit: int,
        cursor: str | None,
    ) -> StatusSubscriptionListResult:
        normalized_limit = max(1, min(limit, 100))
        offset = int(cursor or 0)
        stmt = (
            select(StatusSubscriptionModel)
            .order_by(desc(StatusSubscriptionModel.created_at))
            .offset(offset)
            .limit(normalized_limit + 1)
        )
        if tenant_id:
            stmt = stmt.where(StatusSubscriptionModel.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(StatusSubscriptionModel.status == status)
        async with self._session_factory() as session:
            rows: Sequence[StatusSubscriptionModel] = (await session.execute(stmt)).scalars().all()
        has_more = len(rows) > normalized_limit
        items = rows[:normalized_limit]
        next_cursor = str(offset + normalized_limit) if has_more else None
        return StatusSubscriptionListResult(
            items=[self._to_domain(row) for row in items],
            next_cursor=next_cursor,
        )

    async def mark_active(self, subscription_id: uuid.UUID) -> StatusSubscription | None:
        stmt = (
            update(StatusSubscriptionModel)
            .where(StatusSubscriptionModel.id == subscription_id)
            .values(
                status="active",
                verification_token_hash=None,
                verification_expires_at=None,
                challenge_token_hash=None,
                updated_at=datetime.now(UTC),
            )
            .returning(StatusSubscriptionModel)
        )
        async with self._session_factory() as session:
            record = (await session.execute(stmt)).scalar_one_or_none()
            await session.commit()
        return self._to_domain(record) if record else None

    async def mark_revoked(
        self,
        subscription_id: uuid.UUID,
        *,
        reason: str | None = None,
    ) -> StatusSubscription | None:
        stmt = (
            update(StatusSubscriptionModel)
            .where(StatusSubscriptionModel.id == subscription_id)
            .values(
                status="revoked",
                revoked_at=datetime.now(UTC),
                revoked_reason=reason,
                challenge_token_hash=None,
                verification_token_hash=None,
                verification_expires_at=None,
                updated_at=datetime.now(UTC),
            )
            .returning(StatusSubscriptionModel)
        )
        async with self._session_factory() as session:
            record = (await session.execute(stmt)).scalar_one_or_none()
            await session.commit()
        return self._to_domain(record) if record else None

    async def update_verification_token(
        self,
        subscription_id: uuid.UUID,
        *,
        token_hash: str | None,
        expires_at: datetime | None,
    ) -> StatusSubscription | None:
        stmt = (
            update(StatusSubscriptionModel)
            .where(StatusSubscriptionModel.id == subscription_id)
            .values(
                verification_token_hash=token_hash,
                verification_expires_at=expires_at,
                updated_at=datetime.now(UTC),
            )
            .returning(StatusSubscriptionModel)
        )
        async with self._session_factory() as session:
            record = (await session.execute(stmt)).scalar_one_or_none()
            await session.commit()
        return self._to_domain(record) if record else None

    async def get_delivery_target(self, subscription_id: uuid.UUID) -> str | None:
        async with self._session_factory() as session:
            record = await session.get(StatusSubscriptionModel, subscription_id)
        if not record:
            return None
        return decrypt_optional(self._cipher, record.target_encrypted)

    async def get_webhook_secret(self, subscription_id: uuid.UUID) -> str | None:
        async with self._session_factory() as session:
            record = await session.get(StatusSubscriptionModel, subscription_id)
        if not record:
            return None
        return decrypt_optional(self._cipher, record.webhook_secret_encrypted)

    async def get_unsubscribe_token(self, subscription_id: uuid.UUID) -> str | None:
        async with self._session_factory() as session:
            record = await session.get(StatusSubscriptionModel, subscription_id)
        if not record:
            return None
        return decrypt_optional(self._cipher, record.unsubscribe_token_encrypted)

    async def set_unsubscribe_token(
        self,
        subscription_id: uuid.UUID,
        *,
        token_hash: str,
        token: str,
    ) -> bool:
        stmt = (
            update(StatusSubscriptionModel)
            .where(StatusSubscriptionModel.id == subscription_id)
            .values(
                unsubscribe_token_hash=token_hash,
                unsubscribe_token_encrypted=self._ensure_encrypt(token),
                updated_at=datetime.now(UTC),
            )
        )
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            cursor = cast(CursorResult[Any], result)
            await session.commit()
        return (cursor.rowcount or 0) > 0

    async def find_active_by_target(
        self,
        *,
        channel: str,
        target_hash: str,
        severity_filter: str,
        tenant_id: uuid.UUID | None,
    ) -> StatusSubscription | None:
        conditions = [
            StatusSubscriptionModel.channel == channel,
            StatusSubscriptionModel.target_hash == target_hash,
            StatusSubscriptionModel.severity_filter == severity_filter,
            StatusSubscriptionModel.status == "active",
        ]
        if tenant_id:
            conditions.append(StatusSubscriptionModel.tenant_id == tenant_id)
        else:
            conditions.append(StatusSubscriptionModel.tenant_id.is_(None))
        stmt = select(StatusSubscriptionModel).where(*conditions).limit(1)
        async with self._session_factory() as session:
            record = (await session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(record) if record else None

    def _ensure_encrypt(self, value: str | None) -> bytes | None:
        return encrypt_optional(self._cipher, value)

    def _to_domain(self, row: StatusSubscriptionModel | None) -> StatusSubscription:
        if row is None:
            raise RuntimeError("Subscription row is required.")
        return StatusSubscription(
            id=row.id,
            channel=row.channel,
            target_masked=row.target_masked,
            severity_filter=row.severity_filter,
            status=row.status,
            tenant_id=row.tenant_id,
            metadata=row.metadata_json or {},
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
            verification_expires_at=row.verification_expires_at,
            revoked_at=row.revoked_at,
            unsubscribe_token_hash=row.unsubscribe_token_hash,
        )
