"""Domain models and repository contracts for SSO/OIDC."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol
from uuid import UUID

from app.domain.tenant_roles import TenantRole


class SsoAutoProvisionPolicy(str, Enum):
    """Allowed auto-provisioning policies for SSO logins."""

    DISABLED = "disabled"
    INVITE_ONLY = "invite_only"
    DOMAIN_ALLOWLIST = "domain_allowlist"


class SsoTokenAuthMethod(str, Enum):
    """Supported client authentication methods for the token endpoint."""

    CLIENT_SECRET_POST = "client_secret_post"
    CLIENT_SECRET_BASIC = "client_secret_basic"
    NONE = "none"


@dataclass(slots=True)
class SsoProviderConfig:
    id: UUID
    tenant_id: UUID | None
    provider_key: str
    enabled: bool
    issuer_url: str
    client_id: str
    client_secret: str | None
    discovery_url: str | None
    scopes: list[str]
    pkce_required: bool
    token_endpoint_auth_method: SsoTokenAuthMethod
    allowed_id_token_algs: list[str]
    auto_provision_policy: SsoAutoProvisionPolicy
    allowed_domains: list[str]
    default_role: TenantRole
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class SsoProviderConfigUpsert:
    tenant_id: UUID | None
    provider_key: str
    enabled: bool
    issuer_url: str
    client_id: str
    client_secret: str | None
    discovery_url: str | None
    scopes: list[str]
    pkce_required: bool
    token_endpoint_auth_method: SsoTokenAuthMethod
    allowed_id_token_algs: list[str]
    auto_provision_policy: SsoAutoProvisionPolicy
    allowed_domains: list[str]
    default_role: TenantRole


class SsoProviderConfigRepository(Protocol):
    async def fetch(
        self, *, tenant_id: UUID | None, provider_key: str
    ) -> SsoProviderConfig | None: ...

    async def fetch_with_fallback(
        self, *, tenant_id: UUID | None, provider_key: str
    ) -> SsoProviderConfig | None: ...

    async def list_enabled(
        self, *, tenant_id: UUID | None
    ) -> list[SsoProviderConfig]: ...

    async def list_for_tenant(
        self, *, tenant_id: UUID | None
    ) -> list[SsoProviderConfig]: ...

    async def upsert(self, payload: SsoProviderConfigUpsert) -> SsoProviderConfig: ...

    async def delete(self, *, tenant_id: UUID | None, provider_key: str) -> bool: ...


@dataclass(slots=True)
class UserIdentity:
    id: UUID
    user_id: UUID
    provider_key: str
    issuer: str
    subject: str
    email: str | None
    email_verified: bool
    profile: dict[str, object] | None
    linked_at: datetime
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class UserIdentityUpsert:
    user_id: UUID
    provider_key: str
    issuer: str
    subject: str
    email: str | None
    email_verified: bool
    profile: dict[str, object] | None
    linked_at: datetime
    last_login_at: datetime | None


class UserIdentityRepository(Protocol):
    async def get_by_subject(
        self, *, provider_key: str, issuer: str, subject: str
    ) -> UserIdentity | None: ...

    async def get_by_user(
        self, *, user_id: UUID, provider_key: str
    ) -> UserIdentity | None: ...

    async def upsert(self, payload: UserIdentityUpsert) -> UserIdentity: ...

    async def mark_last_login(self, *, identity_id: UUID, occurred_at: datetime) -> None: ...


__all__ = [
    "SsoAutoProvisionPolicy",
    "SsoTokenAuthMethod",
    "SsoProviderConfig",
    "SsoProviderConfigUpsert",
    "SsoProviderConfigRepository",
    "UserIdentity",
    "UserIdentityUpsert",
    "UserIdentityRepository",
]
