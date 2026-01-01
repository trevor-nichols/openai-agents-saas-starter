"""Postgres repositories for SSO provider configs and identity links."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings, get_settings
from app.domain.sso import (
    SsoAutoProvisionPolicy,
    SsoProviderConfig,
    SsoProviderConfigRepository,
    SsoProviderConfigUpsert,
    SsoTokenAuthMethod,
    UserIdentity,
    UserIdentityRepository,
    UserIdentityUpsert,
)
from app.domain.tenant_roles import TenantRole
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.auth.models.sso import SsoProviderConfigModel, UserIdentityModel
from app.infrastructure.security.cipher import build_cipher, decrypt_optional, encrypt_optional


class PostgresSsoProviderConfigRepository(SsoProviderConfigRepository):
    """Persist SSO provider configs in Postgres with encrypted client secrets."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        encryption_secret: str,
    ) -> None:
        self._session_factory = session_factory
        self._cipher = build_cipher(encryption_secret)
        if self._cipher is None:
            raise ValueError("SSO client secret encryption key is required.")

    async def fetch(
        self,
        *,
        tenant_id: uuid.UUID | None,
        provider_key: str,
    ) -> SsoProviderConfig | None:
        stmt = select(SsoProviderConfigModel).where(
            SsoProviderConfigModel.provider_key == provider_key,
        )
        if tenant_id is None:
            stmt = stmt.where(SsoProviderConfigModel.tenant_id.is_(None))
        else:
            stmt = stmt.where(SsoProviderConfigModel.tenant_id == tenant_id)
        async with self._session_factory() as session:
            record = (await session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(record) if record else None

    async def fetch_with_fallback(
        self,
        *,
        tenant_id: uuid.UUID | None,
        provider_key: str,
    ) -> SsoProviderConfig | None:
        if tenant_id is not None:
            tenant_record = await self.fetch(tenant_id=tenant_id, provider_key=provider_key)
            if tenant_record is not None:
                return tenant_record
        return await self.fetch(tenant_id=None, provider_key=provider_key)

    async def list_enabled(
        self,
        *,
        tenant_id: uuid.UUID | None,
    ) -> list[SsoProviderConfig]:
        records = await self.list_for_tenant(tenant_id=tenant_id)
        return [record for record in records if record.enabled]

    async def list_for_tenant(
        self,
        *,
        tenant_id: uuid.UUID | None,
    ) -> list[SsoProviderConfig]:
        stmt = select(SsoProviderConfigModel)
        if tenant_id is None:
            stmt = stmt.where(SsoProviderConfigModel.tenant_id.is_(None))
        else:
            stmt = stmt.where(SsoProviderConfigModel.tenant_id == tenant_id)
        async with self._session_factory() as session:
            rows = (await session.execute(stmt)).scalars().all()
        return [self._to_domain(row) for row in rows]

    async def upsert(self, payload: SsoProviderConfigUpsert) -> SsoProviderConfig:
        async with self._session_factory() as session:
            stmt = select(SsoProviderConfigModel).where(
                SsoProviderConfigModel.provider_key == payload.provider_key,
            )
            if payload.tenant_id is None:
                stmt = stmt.where(SsoProviderConfigModel.tenant_id.is_(None))
            else:
                stmt = stmt.where(SsoProviderConfigModel.tenant_id == payload.tenant_id)
            record = (await session.execute(stmt)).scalar_one_or_none()

            encrypted_secret = encrypt_optional(self._cipher, payload.client_secret)
            now = datetime.now(UTC)

            if record is None:
                record = SsoProviderConfigModel(
                    id=uuid.uuid4(),
                    tenant_id=payload.tenant_id,
                    provider_key=payload.provider_key,
                    enabled=payload.enabled,
                    issuer_url=payload.issuer_url,
                    client_id=payload.client_id,
                    client_secret_encrypted=encrypted_secret,
                    discovery_url=payload.discovery_url,
                    scopes_json=list(payload.scopes),
                    pkce_required=payload.pkce_required,
                    token_endpoint_auth_method=payload.token_endpoint_auth_method.value,
                    allowed_id_token_algs_json=list(payload.allowed_id_token_algs),
                    auto_provision_policy=payload.auto_provision_policy,
                    allowed_domains_json=list(payload.allowed_domains),
                    default_role=payload.default_role,
                    created_at=now,
                    updated_at=now,
                )
                session.add(record)
            else:
                record.enabled = payload.enabled
                record.issuer_url = payload.issuer_url
                record.client_id = payload.client_id
                record.client_secret_encrypted = encrypted_secret
                record.discovery_url = payload.discovery_url
                record.scopes_json = list(payload.scopes)
                record.pkce_required = payload.pkce_required
                record.token_endpoint_auth_method = payload.token_endpoint_auth_method.value
                record.allowed_id_token_algs_json = list(payload.allowed_id_token_algs)
                record.auto_provision_policy = payload.auto_provision_policy
                record.allowed_domains_json = list(payload.allowed_domains)
                record.default_role = payload.default_role
                record.updated_at = now

            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise RuntimeError("Failed to upsert SSO provider config.") from exc
            await session.refresh(record)
            return self._to_domain(record)

    async def delete(
        self,
        *,
        tenant_id: uuid.UUID | None,
        provider_key: str,
    ) -> bool:
        stmt = (
            update(SsoProviderConfigModel)
            .where(SsoProviderConfigModel.provider_key == provider_key)
            .values(enabled=False, updated_at=datetime.now(UTC))
        )
        if tenant_id is None:
            stmt = stmt.where(SsoProviderConfigModel.tenant_id.is_(None))
        else:
            stmt = stmt.where(SsoProviderConfigModel.tenant_id == tenant_id)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            await session.commit()
            return bool(cast(CursorResult[Any], result).rowcount)

    def _to_domain(self, record: SsoProviderConfigModel) -> SsoProviderConfig:
        client_secret = decrypt_optional(self._cipher, record.client_secret_encrypted)
        return SsoProviderConfig(
            id=record.id,
            tenant_id=record.tenant_id,
            provider_key=record.provider_key,
            enabled=bool(record.enabled),
            issuer_url=record.issuer_url,
            client_id=record.client_id,
            client_secret=client_secret,
            discovery_url=record.discovery_url,
            scopes=list(record.scopes_json or []),
            pkce_required=bool(record.pkce_required),
            token_endpoint_auth_method=_parse_token_auth_method(record.token_endpoint_auth_method),
            allowed_id_token_algs=list(record.allowed_id_token_algs_json or []),
            auto_provision_policy=SsoAutoProvisionPolicy(record.auto_provision_policy.value),
            allowed_domains=list(record.allowed_domains_json or []),
            default_role=cast(TenantRole, record.default_role),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


class PostgresUserIdentityRepository(UserIdentityRepository):
    """Persist user identity links in Postgres."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_subject(
        self, *, provider_key: str, issuer: str, subject: str
    ) -> UserIdentity | None:
        stmt = select(UserIdentityModel).where(
            UserIdentityModel.provider_key == provider_key,
            UserIdentityModel.issuer == issuer,
            UserIdentityModel.subject == subject,
        )
        async with self._session_factory() as session:
            record = (await session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(record) if record else None

    async def get_by_user(
        self, *, user_id: uuid.UUID, provider_key: str
    ) -> UserIdentity | None:
        stmt = select(UserIdentityModel).where(
            UserIdentityModel.user_id == user_id,
            UserIdentityModel.provider_key == provider_key,
        )
        async with self._session_factory() as session:
            record = (await session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(record) if record else None

    async def upsert(self, payload: UserIdentityUpsert) -> UserIdentity:
        async with self._session_factory() as session:
            stmt = select(UserIdentityModel).where(
                UserIdentityModel.provider_key == payload.provider_key,
                UserIdentityModel.issuer == payload.issuer,
                UserIdentityModel.subject == payload.subject,
            )
            record = (await session.execute(stmt)).scalar_one_or_none()
            now = datetime.now(UTC)
            if record is None:
                record = UserIdentityModel(
                    id=uuid.uuid4(),
                    user_id=payload.user_id,
                    provider_key=payload.provider_key,
                    issuer=payload.issuer,
                    subject=payload.subject,
                    email=payload.email,
                    email_verified=payload.email_verified,
                    profile_json=payload.profile,
                    linked_at=payload.linked_at,
                    last_login_at=payload.last_login_at,
                    created_at=now,
                    updated_at=now,
                )
                session.add(record)
            else:
                if record.user_id != payload.user_id:
                    raise RuntimeError("Identity is already linked to a different user.")
                record.email = payload.email
                record.email_verified = payload.email_verified
                record.profile_json = payload.profile
                record.last_login_at = payload.last_login_at or record.last_login_at
                record.updated_at = now
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise RuntimeError("Failed to upsert user identity.") from exc
            await session.refresh(record)
            return self._to_domain(record)

    async def mark_last_login(self, *, identity_id: uuid.UUID, occurred_at: datetime) -> None:
        stmt = (
            update(UserIdentityModel)
            .where(UserIdentityModel.id == identity_id)
            .values(last_login_at=occurred_at, updated_at=occurred_at)
        )
        async with self._session_factory() as session:
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    def _to_domain(record: UserIdentityModel) -> UserIdentity:
        return UserIdentity(
            id=record.id,
            user_id=record.user_id,
            provider_key=record.provider_key,
            issuer=record.issuer,
            subject=record.subject,
            email=record.email,
            email_verified=bool(record.email_verified),
            profile=dict(record.profile_json or {}),
            linked_at=record.linked_at,
            last_login_at=record.last_login_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


def _resolve_encryption_secret(settings: Settings) -> str:
    secret = (
        settings.sso_client_secret_encryption_key
        or settings.auth_session_encryption_key
        or settings.secret_key
    )
    if not secret:
        raise RuntimeError(
            "SSO client secret encryption requires SSO_CLIENT_SECRET_ENCRYPTION_KEY, "
            "AUTH_SESSION_ENCRYPTION_KEY, or SECRET_KEY."
        )
    return secret


def _parse_token_auth_method(raw: str | None) -> SsoTokenAuthMethod:
    if not raw:
        return SsoTokenAuthMethod.CLIENT_SECRET_POST
    try:
        return SsoTokenAuthMethod(raw)
    except ValueError as exc:
        raise ValueError(f"Unsupported token auth method: {raw}") from exc


def get_sso_provider_config_repository(
    settings: Settings | None = None,
) -> PostgresSsoProviderConfigRepository | None:
    resolved = settings or get_settings()
    if not resolved.database_url:
        return None
    session_factory = get_async_sessionmaker()
    secret = _resolve_encryption_secret(resolved)
    return PostgresSsoProviderConfigRepository(
        session_factory,
        encryption_secret=secret,
    )


def get_user_identity_repository(
    settings: Settings | None = None,
) -> PostgresUserIdentityRepository | None:
    resolved = settings or get_settings()
    if not resolved.database_url:
        return None
    session_factory = get_async_sessionmaker()
    return PostgresUserIdentityRepository(session_factory)


__all__ = [
    "PostgresSsoProviderConfigRepository",
    "PostgresUserIdentityRepository",
    "get_sso_provider_config_repository",
    "get_user_identity_repository",
]
