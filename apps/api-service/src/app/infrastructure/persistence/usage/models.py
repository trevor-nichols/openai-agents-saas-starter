"""Usage aggregation ORM models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from app.infrastructure.persistence.auth.models.user import UserAccount
    from app.infrastructure.persistence.tenants.models import TenantAccount


class UsageCounterGranularity(str, Enum):
    """Bucket size for usage summaries."""

    DAY = "day"
    MONTH = "month"


class UsageCounter(Base):
    """Aggregated usage snapshot for billing/analytics."""

    __tablename__ = "usage_counters"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "user_id",
            "period_start",
            "granularity",
            name="uq_usage_counters_bucket",
        ),
        Index("ix_usage_counters_tenant_period", "tenant_id", "period_start"),
        Index("ix_usage_counters_user_period", "user_id", "period_start"),
        Index(
            "uq_usage_counters_tenant_period_null_user",
            "tenant_id",
            "period_start",
            "granularity",
            unique=True,
            postgresql_where=text("user_id IS NULL"),
            sqlite_where=text("user_id IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    granularity: Mapped[UsageCounterGranularity] = mapped_column(
        SAEnum(
            UsageCounterGranularity,
            name="usage_counter_granularity",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    input_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    requests: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    storage_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )

    user: Mapped[UserAccount | None] = relationship("UserAccount")
    tenant: Mapped[TenantAccount] = relationship("TenantAccount")
