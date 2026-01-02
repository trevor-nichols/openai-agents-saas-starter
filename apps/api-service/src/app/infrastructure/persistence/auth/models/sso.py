"""ORM models for SSO provider configs and user identity links."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.sso import SsoAutoProvisionPolicy, SsoTokenAuthMethod
from app.domain.tenant_roles import TenantRole
from app.infrastructure.persistence.models.base import UTC_NOW, Base, uuid_pk
from app.infrastructure.persistence.types import JSONBCompat


class SsoProviderConfigModel(Base):
    __tablename__ = "sso_provider_configs"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "provider_key",
            name="uq_sso_provider_configs_tenant_provider",
        ),
        Index("ix_sso_provider_configs_provider_key", "provider_key"),
        Index(
            "ix_sso_provider_configs_global_provider",
            "provider_key",
            unique=True,
            postgresql_where=text("tenant_id IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_accounts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    provider_key: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    issuer_url: Mapped[str] = mapped_column(String(512), nullable=False)
    client_id: Mapped[str] = mapped_column(String(256), nullable=False)
    client_secret_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    discovery_url: Mapped[str | None] = mapped_column(String(512))
    scopes_json: Mapped[list[str]] = mapped_column(JSONBCompat(), nullable=False, default=list)
    pkce_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    token_endpoint_auth_method: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=SsoTokenAuthMethod.CLIENT_SECRET_POST.value,
    )
    allowed_id_token_algs_json: Mapped[list[str]] = mapped_column(
        JSONBCompat(),
        nullable=False,
        default=list,
    )
    auto_provision_policy: Mapped[SsoAutoProvisionPolicy] = mapped_column(
        SAEnum(
            SsoAutoProvisionPolicy,
            name="sso_auto_provision_policy",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=SsoAutoProvisionPolicy.INVITE_ONLY,
    )
    allowed_domains_json: Mapped[list[str]] = mapped_column(
        JSONBCompat(),
        nullable=False,
        default=list,
    )
    default_role: Mapped[TenantRole] = mapped_column(
        SAEnum(
            TenantRole,
            name="tenant_role",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=TenantRole.MEMBER,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )


class UserIdentityModel(Base):
    __tablename__ = "user_identities"
    __table_args__ = (
        UniqueConstraint(
            "provider_key",
            "issuer",
            "subject",
            name="uq_user_identities_provider_subject",
        ),
        UniqueConstraint(
            "user_id",
            "provider_key",
            name="uq_user_identities_user_provider",
        ),
        Index("ix_user_identities_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_key: Mapped[str] = mapped_column(String(64), nullable=False)
    issuer: Mapped[str] = mapped_column(String(512), nullable=False)
    subject: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    profile_json: Mapped[dict[str, object] | None] = mapped_column(JSONBCompat())
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=UTC_NOW, onupdate=UTC_NOW
    )


__all__ = ["SsoProviderConfigModel", "UserIdentityModel"]
