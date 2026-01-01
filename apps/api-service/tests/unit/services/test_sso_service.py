"""Unit tests for SSO service orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from urllib.parse import parse_qs, urlparse
from uuid import UUID, uuid4

import pytest

from app.core.settings import Settings
from app.domain.auth import UserSessionTokens
from app.domain.sso import (
    SsoAutoProvisionPolicy,
    SsoProviderConfig,
    SsoProviderConfigUpsert,
    SsoTokenAuthMethod,
    UserIdentity,
    UserIdentityUpsert,
)
from app.domain.team import (
    TeamInvite,
    TeamInviteAcceptResult,
    TeamInviteCreate,
    TeamInviteListResult,
    TeamInviteStatus,
    TeamMember,
    TeamMemberListResult,
)
from app.domain.tenant_accounts import (
    TenantAccount,
    TenantAccountCreate,
    TenantAccountListResult,
    TenantAccountStatus,
    TenantAccountStatusUpdate,
    TenantAccountUpdate,
)
from app.domain.tenant_roles import TenantRole
from app.domain.team_errors import TeamMemberAlreadyExistsError
from app.domain.users import (
    PasswordHistoryEntry,
    UserCreatePayload,
    UserLoginEventDTO,
    UserProfilePatch,
    UserRecord,
    UserRepositoryError,
    UserStatus,
)
from app.services.auth_service import AuthService
from app.services.sso.oidc_client import OidcDiscoveryDocument, OidcTokenResponse
from app.services.sso.service import (
    SsoConfigurationError,
    SsoIdentityError,
    SsoProvisioningError,
    SsoService,
    SsoStateError,
    _code_challenge,
)
from app.services.sso.state_store import SsoStatePayload


class FakeStateStore:
    def __init__(self, payload: SsoStatePayload | None = None) -> None:
        self.payload = payload
        self.saved_state: str | None = None
        self.saved_payload: SsoStatePayload | None = None

    async def set_state(self, state: str, payload: SsoStatePayload) -> None:
        self.saved_state = state
        self.saved_payload = payload

    async def consume_state(self, state: str) -> SsoStatePayload | None:
        if self.payload is not None:
            return self.payload
        if self.saved_state != state:
            return None
        payload = self.saved_payload
        self.saved_state = None
        self.saved_payload = None
        return payload


class FakeProviderRepo:
    def __init__(self, config: SsoProviderConfig) -> None:
        self._config = config
        self.tenant_configs: list[SsoProviderConfig] = []
        self.global_configs: list[SsoProviderConfig] = []

    async def fetch_with_fallback(
        self, *, tenant_id: UUID | None, provider_key: str
    ) -> SsoProviderConfig | None:
        record = await self.fetch(tenant_id=tenant_id, provider_key=provider_key)
        if record is not None:
            return record
        if tenant_id is None:
            return None
        return await self.fetch(tenant_id=None, provider_key=provider_key)

    async def fetch(
        self, *, tenant_id: UUID | None, provider_key: str
    ) -> SsoProviderConfig | None:
        configs = self.global_configs if tenant_id is None else self.tenant_configs
        for config in configs:
            if config.provider_key == provider_key:
                return config
        if self._config.provider_key == provider_key and self._config.tenant_id == tenant_id:
            return self._config
        return None

    async def list_enabled(self, *, tenant_id: UUID | None) -> list[SsoProviderConfig]:
        records = await self.list_for_tenant(tenant_id=tenant_id)
        return [record for record in records if record.enabled]

    async def list_for_tenant(self, *, tenant_id: UUID | None) -> list[SsoProviderConfig]:
        configs = self.global_configs if tenant_id is None else self.tenant_configs
        if configs:
            return list(configs)
        if self._config.tenant_id == tenant_id:
            return [self._config]
        return []

    async def upsert(self, payload: SsoProviderConfigUpsert) -> SsoProviderConfig:
        now = datetime.now(UTC)
        config = SsoProviderConfig(
            id=uuid4(),
            tenant_id=payload.tenant_id,
            provider_key=payload.provider_key,
            enabled=payload.enabled,
            issuer_url=payload.issuer_url,
            client_id=payload.client_id,
            client_secret=payload.client_secret,
            discovery_url=payload.discovery_url,
            scopes=list(payload.scopes),
            pkce_required=payload.pkce_required,
            token_endpoint_auth_method=payload.token_endpoint_auth_method,
            allowed_id_token_algs=list(payload.allowed_id_token_algs),
            auto_provision_policy=payload.auto_provision_policy,
            allowed_domains=list(payload.allowed_domains),
            default_role=payload.default_role,
            created_at=now,
            updated_at=now,
        )
        target = self.global_configs if payload.tenant_id is None else self.tenant_configs
        target[:] = [item for item in target if item.provider_key != payload.provider_key]
        target.append(config)
        self._config = config
        return config

    async def delete(self, *, tenant_id: UUID | None, provider_key: str) -> bool:
        configs = self.global_configs if tenant_id is None else self.tenant_configs
        for config in configs:
            if config.provider_key == provider_key:
                config.enabled = False
                return True
        if self._config.provider_key == provider_key and self._config.tenant_id == tenant_id:
            self._config.enabled = False
            return True
        return False


class FakeIdentityRepo:
    def __init__(self, identity: UserIdentity | None = None) -> None:
        self.identity = identity
        self.by_user: dict[UUID, UserIdentity] = {}
        self.upserts: list[UserIdentityUpsert] = []

    async def get_by_subject(
        self, *, provider_key: str, issuer: str, subject: str
    ) -> UserIdentity | None:
        return self.identity

    async def get_by_user(self, *, user_id: UUID, provider_key: str) -> UserIdentity | None:
        return self.by_user.get(user_id)

    async def upsert(self, payload: UserIdentityUpsert) -> UserIdentity:
        self.upserts.append(payload)
        identity = UserIdentity(
            id=uuid4(),
            user_id=payload.user_id,
            provider_key=payload.provider_key,
            issuer=payload.issuer,
            subject=payload.subject,
            email=payload.email,
            email_verified=payload.email_verified,
            profile=payload.profile,
            linked_at=payload.linked_at,
            last_login_at=payload.last_login_at,
            created_at=payload.linked_at,
            updated_at=payload.linked_at,
        )
        self.by_user[payload.user_id] = identity
        return identity

    async def mark_last_login(self, *, identity_id: UUID, occurred_at: datetime) -> None:
        for identity in self.by_user.values():
            if identity.id == identity_id:
                identity.last_login_at = occurred_at
                return None
        if self.identity and self.identity.id == identity_id:
            self.identity.last_login_at = occurred_at
        return None


class FakeUserRepo:
    def __init__(
        self,
        user: UserRecord | None = None,
        *,
        raise_on_create: Exception | None = None,
        deferred_user: UserRecord | None = None,
    ) -> None:
        self.user = user
        self.by_id: dict[UUID, UserRecord] = {}
        self.by_email: dict[str, UserRecord] = {}
        self.raise_on_create = raise_on_create
        self.deferred_user = deferred_user
        if user:
            self.by_id[user.id] = user
            self.by_email[user.email] = user
        self.created: list[UserCreatePayload] = []
        self.verified: list[UUID] = []
        self.profile_updates: list[tuple[UUID, UserProfilePatch, set[str]]] = []

    async def get_user_by_id(self, user_id: UUID) -> UserRecord | None:
        return self.by_id.get(user_id)

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        return self.by_email.get(email)

    async def create_user(self, payload: UserCreatePayload) -> UserRecord:
        if self.raise_on_create:
            if self.deferred_user:
                self.by_id[self.deferred_user.id] = self.deferred_user
                self.by_email[self.deferred_user.email] = self.deferred_user
            raise self.raise_on_create
        self.created.append(payload)
        record = _build_user(payload.email, user_id=uuid4())
        self.user = record
        self.by_id[record.id] = record
        self.by_email[record.email] = record
        return record

    async def update_user_status(self, user_id: UUID, status: UserStatus) -> None:
        if self.user and self.user.id == user_id:
            self.user.status = status

    async def update_user_email(self, user_id: UUID, new_email: str) -> None:
        record = self.by_id.get(user_id)
        if record:
            if record.email in self.by_email:
                self.by_email.pop(record.email, None)
            record.email = new_email
            self.by_email[new_email] = record

    async def record_login_event(self, event: UserLoginEventDTO) -> None:
        return None

    async def list_password_history(
        self, user_id: UUID, limit: int = 5
    ) -> list[PasswordHistoryEntry]:
        return []

    async def add_password_history(self, entry: PasswordHistoryEntry) -> None:
        return None

    async def trim_password_history(self, user_id: UUID, keep: int) -> None:
        return None

    async def increment_lockout_counter(self, user_id: UUID, *, ttl_seconds: int) -> int:
        return 0

    async def reset_lockout_counter(self, user_id: UUID) -> None:
        return None

    async def mark_user_locked(self, user_id: UUID, *, duration_seconds: int) -> None:
        return None

    async def clear_user_lock(self, user_id: UUID) -> None:
        return None

    async def is_user_locked(self, user_id: UUID) -> bool:
        return False

    async def update_password_hash(
        self,
        user_id: UUID,
        password_hash: str,
        *,
        password_pepper_version: str,
    ) -> None:
        if self.user and self.user.id == user_id:
            self.user.password_hash = password_hash
            self.user.password_pepper_version = password_pepper_version

    async def mark_email_verified(self, user_id: UUID, *, timestamp: datetime) -> None:
        self.verified.append(user_id)

    async def list_sole_owner_tenant_ids(self, user_id: UUID) -> list[UUID]:
        return []

    async def upsert_user_profile(
        self,
        user_id: UUID,
        update: UserProfilePatch,
        *,
        provided_fields: set[str],
    ) -> None:
        self.profile_updates.append((user_id, update, provided_fields))


class FakeMembershipRepo:
    def __init__(self, exists: bool = False) -> None:
        self.exists = exists
        self.added: list[tuple[UUID, UUID, TenantRole]] = []

    async def membership_exists(self, *, tenant_id: UUID, user_id: UUID) -> bool:
        return self.exists

    async def add_member(self, *, tenant_id: UUID, user_id: UUID, role: TenantRole) -> TeamMember:
        self.added.append((tenant_id, user_id, role))
        return TeamMember(
            user_id=user_id,
            tenant_id=tenant_id,
            email="member@example.com",
            display_name=None,
            role=role,
            status=UserStatus.ACTIVE,
            email_verified=True,
            joined_at=datetime.now(UTC),
        )

    async def list_members(
        self,
        *,
        tenant_id: UUID,
        limit: int,
        offset: int,
    ) -> TeamMemberListResult:
        return TeamMemberListResult(members=[], total=0, owner_count=0)

    async def get_member(self, *, tenant_id: UUID, user_id: UUID) -> TeamMember | None:
        return None

    async def update_role(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        role: TenantRole,
    ) -> TeamMember | None:
        return None

    async def remove_member(self, *, tenant_id: UUID, user_id: UUID) -> bool:
        return False

    async def count_members_by_role(self, *, tenant_id: UUID, role: TenantRole) -> int:
        return 0


class FakeInviteRepo:
    def __init__(self, invites: list[TeamInvite]) -> None:
        self.invites = invites

    async def create(self, payload: TeamInviteCreate) -> TeamInvite:
        invite = TeamInvite(
            id=uuid4(),
            tenant_id=payload.tenant_id,
            token_hash=payload.token_hash,
            token_hint=payload.token_hint,
            invited_email=payload.invited_email,
            role=payload.role,
            status=TeamInviteStatus.ACTIVE,
            created_by_user_id=payload.created_by_user_id,
            accepted_by_user_id=None,
            accepted_at=None,
            revoked_at=None,
            revoked_reason=None,
            expires_at=payload.expires_at,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.invites.append(invite)
        return invite

    async def get(self, invite_id: UUID) -> TeamInvite | None:
        for invite in self.invites:
            if invite.id == invite_id:
                return invite
        return None

    async def find_by_token_hash(self, token_hash: str) -> TeamInvite | None:
        for invite in self.invites:
            if invite.token_hash == token_hash:
                return invite
        return None

    async def list_invites(
        self,
        *,
        tenant_id: UUID,
        status: TeamInviteStatus | None,
        email: str | None,
        limit: int,
        offset: int,
    ) -> TeamInviteListResult:
        return TeamInviteListResult(invites=self.invites, total=len(self.invites))

    async def mark_revoked(
        self,
        invite_id: UUID,
        *,
        tenant_id: UUID,
        timestamp: datetime,
        reason: str | None,
    ) -> TeamInvite | None:
        invite = await self.get(invite_id)
        if invite is None:
            return None
        invite.status = TeamInviteStatus.REVOKED
        invite.revoked_at = timestamp
        invite.revoked_reason = reason
        invite.updated_at = timestamp
        return invite

    async def mark_accepted(
        self,
        invite_id: UUID,
        *,
        timestamp: datetime,
        accepted_by_user_id: UUID,
    ) -> TeamInvite | None:
        invite = await self.get(invite_id)
        if invite is None:
            return None
        invite.status = TeamInviteStatus.ACCEPTED
        invite.accepted_at = timestamp
        invite.accepted_by_user_id = accepted_by_user_id
        invite.updated_at = timestamp
        return invite

    async def mark_expired(self, invite_id: UUID, *, timestamp: datetime) -> TeamInvite | None:
        invite = await self.get(invite_id)
        if invite is None:
            return None
        invite.status = TeamInviteStatus.EXPIRED
        invite.updated_at = timestamp
        return invite


class FakeInviteAcceptanceRepo:
    def __init__(
        self,
        *,
        new_user_id: UUID | None = None,
        raise_existing: Exception | None = None,
    ) -> None:
        self.accepted_existing: list[tuple[str, UUID]] = []
        self.accepted_new: list[str] = []
        self.new_user_id = new_user_id or uuid4()
        self.raise_existing = raise_existing

    async def accept_for_existing_user(
        self, *, token_hash: str, user_id: UUID, now: datetime
    ) -> TeamInvite:
        if self.raise_existing:
            raise self.raise_existing
        self.accepted_existing.append((token_hash, user_id))
        return _build_invite(tenant_id=uuid4(), token_hash=token_hash)

    async def accept_for_new_user(
        self,
        *,
        token_hash: str,
        password_hash: str,
        password_pepper_version: str,
        display_name: str | None,
        now: datetime,
    ) -> TeamInviteAcceptResult:
        self.accepted_new.append(token_hash)
        return TeamInviteAcceptResult(
            invite_id=uuid4(),
            user_id=self.new_user_id,
            tenant_id=uuid4(),
            email="owner@example.com",
        )


class FakeTenantRepo:
    def __init__(self, tenant: TenantAccount) -> None:
        self.tenant = tenant

    async def get(self, tenant_id: UUID) -> TenantAccount | None:
        if tenant_id == self.tenant.id:
            return self.tenant
        return None

    async def get_by_slug(self, slug: str) -> TenantAccount | None:
        if slug == self.tenant.slug:
            return self.tenant
        return None

    async def get_name(self, tenant_id: UUID) -> str | None:
        if tenant_id == self.tenant.id:
            return self.tenant.name
        return None

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        status: TenantAccountStatus | None = None,
        query: str | None = None,
    ) -> TenantAccountListResult:
        if status and self.tenant.status != status:
            return TenantAccountListResult(accounts=[], total=0)
        return TenantAccountListResult(accounts=[self.tenant], total=1)

    async def create(self, payload: TenantAccountCreate) -> TenantAccount:
        now = datetime.now(UTC)
        self.tenant = TenantAccount(
            id=uuid4(),
            slug=payload.slug,
            name=payload.name,
            status=payload.status,
            created_at=now,
            updated_at=now,
        )
        return self.tenant

    async def update(self, tenant_id: UUID, update: TenantAccountUpdate) -> TenantAccount | None:
        if tenant_id != self.tenant.id:
            return None
        if update.name is not None:
            self.tenant.name = update.name
        if update.slug is not None:
            self.tenant.slug = update.slug
        self.tenant.updated_at = datetime.now(UTC)
        return self.tenant

    async def update_status(
        self, tenant_id: UUID, update: TenantAccountStatusUpdate
    ) -> TenantAccount | None:
        if tenant_id != self.tenant.id:
            return None
        self.tenant.status = update.status
        self.tenant.updated_at = datetime.now(UTC)
        return self.tenant


class FakeAuthService(AuthService):
    def __init__(self, tokens: UserSessionTokens) -> None:
        self.tokens = tokens

    async def issue_user_session(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
        reason: str = "sso",
        enforce_mfa: bool = True,
    ) -> UserSessionTokens:
        return self.tokens


class FakeOidcClient:
    def __init__(self, *, claims: dict[str, Any], discovery: OidcDiscoveryDocument) -> None:
        self.claims = claims
        self.discovery = discovery

    async def fetch_discovery(
        self,
        issuer_url: str,
        *,
        discovery_url: str | None = None,
    ) -> OidcDiscoveryDocument:
        return self.discovery

    async def exchange_code_for_tokens(
        self,
        *,
        token_endpoint: str,
        client_id: str,
        client_secret: str | None,
        code: str,
        redirect_uri: str,
        code_verifier: str | None,
        token_auth_method: str,
    ) -> OidcTokenResponse:
        return OidcTokenResponse(
            id_token="id-token",
            access_token=None,
            refresh_token=None,
            expires_in=None,
            token_type=None,
            scope=None,
        )

    async def verify_id_token(
        self,
        *,
        id_token: str,
        issuer: str,
        audience: str,
        jwks_uri: str,
        allowed_algs: list[str] | None = None,
        clock_skew_seconds: int = 60,
    ) -> dict[str, Any]:
        return self.claims

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_start_sso_builds_authorize_url_and_stores_state() -> None:
    tenant = _build_tenant()
    config = _build_config(tenant_id=tenant.id)
    state_store = FakeStateStore()
    provider_repo = FakeProviderRepo(config)

    discovery = OidcDiscoveryDocument(
        issuer=config.issuer_url,
        authorization_endpoint="https://auth.example.com/authorize",
        token_endpoint="https://auth.example.com/token",
        jwks_uri="https://auth.example.com/jwks",
    )

    service = _service(
        tenant=tenant,
        state_store=state_store,
        provider_repo=provider_repo,
        oidc_factory=lambda: FakeOidcClient(claims={}, discovery=discovery),
    )

    result = await service.start_sso(
        provider_key="google",
        tenant_id=tenant.id,
        tenant_slug=None,
        login_hint="owner@example.com",
    )

    assert result.authorize_url.startswith(discovery.authorization_endpoint)
    assert state_store.saved_state is not None
    assert state_store.saved_payload is not None

    params = parse_qs(urlparse(result.authorize_url).query)
    assert params["client_id"][0] == config.client_id
    assert params["state"][0] == state_store.saved_state
    assert params["nonce"][0] == state_store.saved_payload.nonce
    assert params["redirect_uri"][0].endswith("/auth/sso/google/callback")
    assert params["login_hint"][0] == "owner@example.com"
    assert state_store.saved_payload.pkce_verifier is not None
    assert params["code_challenge"][0] == _code_challenge(
        state_store.saved_payload.pkce_verifier
    )


@pytest.mark.asyncio
async def test_complete_sso_rejects_invalid_state() -> None:
    tenant = _build_tenant()
    config = _build_config(tenant_id=tenant.id)
    state_store = FakeStateStore(payload=None)
    service = _service(
        tenant=tenant,
        state_store=state_store,
        provider_repo=FakeProviderRepo(config),
        oidc_factory=lambda: FakeOidcClient(claims={}, discovery=_discovery(config)),
    )

    with pytest.raises(SsoStateError):
        await service.complete_sso(provider_key="google", code="code", state="missing")


@pytest.mark.asyncio
async def test_complete_sso_rejects_unsupported_token_auth_method() -> None:
    tenant = _build_tenant()
    config = _build_config(tenant_id=tenant.id)
    config.token_endpoint_auth_method = SsoTokenAuthMethod.CLIENT_SECRET_BASIC

    state_payload = SsoStatePayload(
        tenant_id=str(tenant.id),
        provider_key="google",
        pkce_verifier="verifier",
        nonce="nonce",
        redirect_uri="https://app.example.com/auth/sso/google/callback",
        scopes=["openid", "email"],
    )
    state_store = FakeStateStore(payload=state_payload)

    discovery = OidcDiscoveryDocument(
        issuer=config.issuer_url,
        authorization_endpoint="https://auth.example.com/authorize",
        token_endpoint="https://auth.example.com/token",
        jwks_uri="https://auth.example.com/jwks",
        token_endpoint_auth_methods_supported=["client_secret_post"],
    )

    service = _service(
        tenant=tenant,
        config=config,
        state_store=state_store,
        provider_repo=FakeProviderRepo(config),
        oidc_factory=lambda: FakeOidcClient(claims={}, discovery=discovery),
    )

    with pytest.raises(SsoConfigurationError):
        await service.complete_sso(provider_key="google", code="code", state="state")


@pytest.mark.asyncio
async def test_complete_sso_rejects_invalid_id_token_algs() -> None:
    tenant = _build_tenant()
    config = _build_config(tenant_id=tenant.id)
    config.allowed_id_token_algs = ["HS256"]

    state_payload = SsoStatePayload(
        tenant_id=str(tenant.id),
        provider_key="google",
        pkce_verifier="verifier",
        nonce="nonce",
        redirect_uri="https://app.example.com/auth/sso/google/callback",
        scopes=["openid", "email"],
    )
    state_store = FakeStateStore(payload=state_payload)

    claims = {
        "sub": "subject",
        "email": "owner@example.com",
        "email_verified": True,
        "nonce": "nonce",
        "iss": config.issuer_url,
    }

    service = _service(
        tenant=tenant,
        config=config,
        state_store=state_store,
        provider_repo=FakeProviderRepo(config),
        oidc_factory=lambda: FakeOidcClient(claims=claims, discovery=_discovery(config)),
    )

    with pytest.raises(SsoConfigurationError):
        await service.complete_sso(provider_key="google", code="code", state="state")


@pytest.mark.asyncio
async def test_complete_sso_invite_only_accepts_existing_user() -> None:
    tenant = _build_tenant()
    config = _build_config(tenant_id=tenant.id, policy=SsoAutoProvisionPolicy.INVITE_ONLY)
    user = _build_user("owner@example.com")
    invite = _build_invite(tenant_id=tenant.id, token_hash="token-hash")

    state_payload = SsoStatePayload(
        tenant_id=str(tenant.id),
        provider_key="google",
        pkce_verifier="verifier",
        nonce="nonce",
        redirect_uri="https://app.example.com/auth/sso/google/callback",
        scopes=["openid", "email"],
    )
    state_store = FakeStateStore(payload=state_payload)

    claims = {
        "sub": "subject",
        "email": "owner@example.com",
        "email_verified": True,
        "nonce": "nonce",
        "iss": config.issuer_url,
        "name": "Owner",
    }

    identity_repo = FakeIdentityRepo()
    user_repo = FakeUserRepo(user)
    membership_repo = FakeMembershipRepo(exists=False)
    invite_repo = FakeInviteRepo([invite])
    invite_acceptance_repo = FakeInviteAcceptanceRepo()
    tokens = _tokens()

    service = _service(
        tenant=tenant,
        config=config,
        state_store=state_store,
        provider_repo=FakeProviderRepo(config),
        identity_repo=identity_repo,
        user_repo=user_repo,
        membership_repo=membership_repo,
        invite_repo=invite_repo,
        invite_acceptance_repo=invite_acceptance_repo,
        auth_service=FakeAuthService(tokens),
        oidc_factory=lambda: FakeOidcClient(claims=claims, discovery=_discovery(config)),
    )

    result = await service.complete_sso(
        provider_key="google",
        code="code",
        state="state",
        ip_address=None,
        user_agent=None,
    )

    assert result.access_token == tokens.access_token
    assert invite_acceptance_repo.accepted_existing
    assert user.id in user_repo.verified
    assert identity_repo.upserts


@pytest.mark.asyncio
async def test_complete_sso_invite_only_handles_membership_race() -> None:
    tenant = _build_tenant()
    config = _build_config(tenant_id=tenant.id, policy=SsoAutoProvisionPolicy.INVITE_ONLY)
    user = _build_user("owner@example.com")
    invite = _build_invite(tenant_id=tenant.id, token_hash="token-hash")

    state_payload = SsoStatePayload(
        tenant_id=str(tenant.id),
        provider_key="google",
        pkce_verifier="verifier",
        nonce="nonce",
        redirect_uri="https://app.example.com/auth/sso/google/callback",
        scopes=["openid", "email"],
    )
    state_store = FakeStateStore(payload=state_payload)

    claims = {
        "sub": "subject",
        "email": "owner@example.com",
        "email_verified": True,
        "nonce": "nonce",
        "iss": config.issuer_url,
    }

    invite_repo = FakeInviteRepo([invite])
    invite_acceptance_repo = FakeInviteAcceptanceRepo(
        raise_existing=TeamMemberAlreadyExistsError("User is already a member of this tenant.")
    )
    tokens = _tokens()

    service = _service(
        tenant=tenant,
        config=config,
        state_store=state_store,
        provider_repo=FakeProviderRepo(config),
        user_repo=FakeUserRepo(user),
        membership_repo=FakeMembershipRepo(exists=False),
        invite_repo=invite_repo,
        invite_acceptance_repo=invite_acceptance_repo,
        auth_service=FakeAuthService(tokens),
        oidc_factory=lambda: FakeOidcClient(claims=claims, discovery=_discovery(config)),
    )

    result = await service.complete_sso(
        provider_key="google",
        code="code",
        state="state",
    )

    assert result.access_token == tokens.access_token
    assert invite.status == TeamInviteStatus.ACCEPTED


@pytest.mark.asyncio
async def test_complete_sso_domain_allowlist_provisions_new_user() -> None:
    tenant = _build_tenant()
    config = _build_config(
        tenant_id=tenant.id,
        policy=SsoAutoProvisionPolicy.DOMAIN_ALLOWLIST,
        allowed_domains=["example.com"],
    )

    state_payload = SsoStatePayload(
        tenant_id=str(tenant.id),
        provider_key="google",
        pkce_verifier="verifier",
        nonce="nonce",
        redirect_uri="https://app.example.com/auth/sso/google/callback",
        scopes=["openid", "email"],
    )
    state_store = FakeStateStore(payload=state_payload)

    claims = {
        "sub": "subject",
        "email": "new@example.com",
        "email_verified": True,
        "nonce": "nonce",
        "iss": config.issuer_url,
    }

    user_repo = FakeUserRepo(None)
    tokens = _tokens()

    service = _service(
        tenant=tenant,
        config=config,
        state_store=state_store,
        provider_repo=FakeProviderRepo(config),
        user_repo=user_repo,
        membership_repo=FakeMembershipRepo(exists=False),
        auth_service=FakeAuthService(tokens),
        oidc_factory=lambda: FakeOidcClient(claims=claims, discovery=_discovery(config)),
    )

    result = await service.complete_sso(
        provider_key="google",
        code="code",
        state="state",
    )

    assert result.refresh_token == tokens.refresh_token
    assert user_repo.created
    assert user_repo.verified


@pytest.mark.asyncio
async def test_complete_sso_domain_allowlist_logs_provisioned_for_existing_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.sso.service as sso_service_mod

    tenant = _build_tenant()
    config = _build_config(
        tenant_id=tenant.id,
        policy=SsoAutoProvisionPolicy.DOMAIN_ALLOWLIST,
        allowed_domains=["example.com"],
    )
    user = _build_user("owner@example.com")

    state_payload = SsoStatePayload(
        tenant_id=str(tenant.id),
        provider_key="google",
        pkce_verifier="verifier",
        nonce="nonce",
        redirect_uri="https://app.example.com/auth/sso/google/callback",
        scopes=["openid", "email"],
    )
    state_store = FakeStateStore(payload=state_payload)

    claims = {
        "sub": "subject",
        "email": "owner@example.com",
        "email_verified": True,
        "nonce": "nonce",
        "iss": config.issuer_url,
    }

    events: list[tuple[str, dict[str, object]]] = []

    def fake_log_event(event: str, **fields: object) -> None:
        events.append((event, dict(fields)))

    monkeypatch.setattr(sso_service_mod, "log_event", fake_log_event)

    service = _service(
        tenant=tenant,
        config=config,
        state_store=state_store,
        provider_repo=FakeProviderRepo(config),
        identity_repo=FakeIdentityRepo(),
        user_repo=FakeUserRepo(user),
        membership_repo=FakeMembershipRepo(exists=False),
        auth_service=FakeAuthService(_tokens()),
        oidc_factory=lambda: FakeOidcClient(claims=claims, discovery=_discovery(config)),
    )

    await service.complete_sso(
        provider_key="google",
        code="code",
        state="state",
    )

    assert any(
        event == "auth.sso.provisioned"
        and payload.get("policy") == "domain_allowlist"
        and payload.get("user_id") == str(user.id)
        for event, payload in events
    )


@pytest.mark.asyncio
async def test_complete_sso_domain_allowlist_handles_user_creation_race() -> None:
    tenant = _build_tenant()
    config = _build_config(
        tenant_id=tenant.id,
        policy=SsoAutoProvisionPolicy.DOMAIN_ALLOWLIST,
        allowed_domains=["example.com"],
    )
    existing_user = _build_user("owner@example.com")

    state_payload = SsoStatePayload(
        tenant_id=str(tenant.id),
        provider_key="google",
        pkce_verifier="verifier",
        nonce="nonce",
        redirect_uri="https://app.example.com/auth/sso/google/callback",
        scopes=["openid", "email"],
    )
    state_store = FakeStateStore(payload=state_payload)

    claims = {
        "sub": "subject",
        "email": "owner@example.com",
        "email_verified": True,
        "nonce": "nonce",
        "iss": config.issuer_url,
    }

    user_repo = FakeUserRepo(
        raise_on_create=UserRepositoryError("duplicate email"),
        deferred_user=existing_user,
    )
    membership_repo = FakeMembershipRepo(exists=False)
    tokens = _tokens()

    service = _service(
        tenant=tenant,
        config=config,
        state_store=state_store,
        provider_repo=FakeProviderRepo(config),
        user_repo=user_repo,
        membership_repo=membership_repo,
        auth_service=FakeAuthService(tokens),
        oidc_factory=lambda: FakeOidcClient(claims=claims, discovery=_discovery(config)),
    )

    result = await service.complete_sso(
        provider_key="google",
        code="code",
        state="state",
    )

    assert result.refresh_token == tokens.refresh_token
    assert membership_repo.added
    assert existing_user.id in user_repo.verified


@pytest.mark.asyncio
async def test_complete_sso_invite_only_provisions_new_user() -> None:
    tenant = _build_tenant()
    config = _build_config(tenant_id=tenant.id, policy=SsoAutoProvisionPolicy.INVITE_ONLY)

    state_payload = SsoStatePayload(
        tenant_id=str(tenant.id),
        provider_key="google",
        pkce_verifier="verifier",
        nonce="nonce",
        redirect_uri="https://app.example.com/auth/sso/google/callback",
        scopes=["openid", "email"],
    )
    state_store = FakeStateStore(payload=state_payload)

    claims = {
        "sub": "subject",
        "email": "new@example.com",
        "email_verified": True,
        "nonce": "nonce",
        "iss": config.issuer_url,
    }

    new_user_id = uuid4()
    user_repo = FakeUserRepo(None)
    user_repo.by_id[new_user_id] = _build_user("new@example.com", user_id=new_user_id)
    invite = _build_invite(tenant_id=tenant.id, token_hash="token-hash")
    invite_repo = FakeInviteRepo([invite])
    invite_acceptance_repo = FakeInviteAcceptanceRepo(new_user_id=new_user_id)
    tokens = _tokens()

    service = _service(
        tenant=tenant,
        config=config,
        state_store=state_store,
        provider_repo=FakeProviderRepo(config),
        user_repo=user_repo,
        membership_repo=FakeMembershipRepo(exists=False),
        invite_repo=invite_repo,
        invite_acceptance_repo=invite_acceptance_repo,
        auth_service=FakeAuthService(tokens),
        oidc_factory=lambda: FakeOidcClient(claims=claims, discovery=_discovery(config)),
    )

    result = await service.complete_sso(
        provider_key="google",
        code="code",
        state="state",
    )

    assert result.access_token == tokens.access_token
    assert invite_acceptance_repo.accepted_new
    assert new_user_id in user_repo.verified


@pytest.mark.asyncio
async def test_complete_sso_domain_allowlist_rejects_unknown_domain() -> None:
    tenant = _build_tenant()
    config = _build_config(
        tenant_id=tenant.id,
        policy=SsoAutoProvisionPolicy.DOMAIN_ALLOWLIST,
        allowed_domains=["example.com"],
    )
    state_store = FakeStateStore(
        payload=SsoStatePayload(
            tenant_id=str(tenant.id),
            provider_key="google",
            pkce_verifier="verifier",
            nonce="nonce",
            redirect_uri="https://app.example.com/auth/sso/google/callback",
            scopes=["openid", "email"],
        )
    )
    claims = {
        "sub": "subject",
        "email": "blocked@other.com",
        "email_verified": True,
        "nonce": "nonce",
        "iss": config.issuer_url,
    }

    service = _service(
        tenant=tenant,
        config=config,
        state_store=state_store,
        provider_repo=FakeProviderRepo(config),
        membership_repo=FakeMembershipRepo(exists=False),
        oidc_factory=lambda: FakeOidcClient(claims=claims, discovery=_discovery(config)),
    )

    with pytest.raises(SsoProvisioningError):
        await service.complete_sso(provider_key="google", code="code", state="state")


@pytest.mark.asyncio
async def test_complete_sso_rejects_identity_conflict() -> None:
    tenant = _build_tenant()
    config = _build_config(tenant_id=tenant.id)
    user = _build_user("owner@example.com")
    existing_identity = UserIdentity(
        id=uuid4(),
        user_id=user.id,
        provider_key="google",
        issuer="https://accounts.google.com",
        subject="old-subject",
        email="owner@example.com",
        email_verified=True,
        profile=None,
        linked_at=datetime.now(UTC),
        last_login_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    identity_repo = FakeIdentityRepo(identity=None)
    identity_repo.by_user[user.id] = existing_identity

    state_store = FakeStateStore(
        payload=SsoStatePayload(
            tenant_id=str(tenant.id),
            provider_key="google",
            pkce_verifier="verifier",
            nonce="nonce",
            redirect_uri="https://app.example.com/auth/sso/google/callback",
            scopes=["openid", "email"],
        )
    )
    claims = {
        "sub": "new-subject",
        "email": "owner@example.com",
        "email_verified": True,
        "nonce": "nonce",
        "iss": config.issuer_url,
    }

    service = _service(
        tenant=tenant,
        config=config,
        state_store=state_store,
        provider_repo=FakeProviderRepo(config),
        identity_repo=identity_repo,
        user_repo=FakeUserRepo(user),
        membership_repo=FakeMembershipRepo(exists=True),
        oidc_factory=lambda: FakeOidcClient(claims=claims, discovery=_discovery(config)),
    )

    with pytest.raises(SsoIdentityError):
        await service.complete_sso(provider_key="google", code="code", state="state")


@pytest.mark.asyncio
async def test_list_providers_merges_tenant_and_global_configs() -> None:
    tenant = _build_tenant()
    config = _build_config(tenant_id=tenant.id)
    provider_repo = FakeProviderRepo(config)

    provider_repo.global_configs = [
        _build_config(tenant_id=None, provider_key="google"),
        _build_config(tenant_id=None, provider_key="okta"),
    ]
    provider_repo.tenant_configs = [
        _build_config(tenant_id=tenant.id, provider_key="google", client_id="tenant"),
    ]

    service = _service(
        tenant=tenant,
        state_store=FakeStateStore(),
        provider_repo=provider_repo,
    )

    providers = await service.list_providers(tenant_id=tenant.id, tenant_slug=None)
    keys = [item.provider_key for item in providers]

    assert keys == ["google", "okta"]
    assert providers[0].client_id == "tenant"


@pytest.mark.asyncio
async def test_list_providers_suppresses_disabled_tenant_override() -> None:
    tenant = _build_tenant()
    config = _build_config(tenant_id=tenant.id)
    provider_repo = FakeProviderRepo(config)

    provider_repo.global_configs = [
        _build_config(tenant_id=None, provider_key="google"),
        _build_config(tenant_id=None, provider_key="okta"),
    ]
    provider_repo.tenant_configs = [
        _build_config(tenant_id=tenant.id, provider_key="google", enabled=False),
    ]

    service = _service(
        tenant=tenant,
        state_store=FakeStateStore(),
        provider_repo=provider_repo,
    )

    providers = await service.list_providers(tenant_id=tenant.id, tenant_slug=None)
    keys = [item.provider_key for item in providers]

    assert keys == ["okta"]


def _settings() -> Settings:
    settings = SimpleNamespace(
        app_public_url="https://app.example.com",
        sso_clock_skew_seconds=60,
    )
    return cast(Settings, settings)


def _service(
    *,
    tenant: TenantAccount,
    config: SsoProviderConfig | None = None,
    state_store: FakeStateStore | None = None,
    provider_repo: FakeProviderRepo | None = None,
    identity_repo: FakeIdentityRepo | None = None,
    user_repo: FakeUserRepo | None = None,
    membership_repo: FakeMembershipRepo | None = None,
    invite_repo: FakeInviteRepo | None = None,
    invite_acceptance_repo: FakeInviteAcceptanceRepo | None = None,
    tenant_repo: FakeTenantRepo | None = None,
    auth_service: FakeAuthService | None = None,
    oidc_factory=None,
) -> SsoService:
    return SsoService(
        settings_factory=_settings,
        state_store=state_store or FakeStateStore(),
        provider_repository=provider_repo or FakeProviderRepo(config or _build_config(tenant.id)),
        identity_repository=identity_repo or FakeIdentityRepo(),
        user_repository=user_repo or FakeUserRepo(None),
        membership_repository=membership_repo or FakeMembershipRepo(exists=True),
        invite_repository=invite_repo or FakeInviteRepo([]),
        invite_acceptance_repository=invite_acceptance_repo or FakeInviteAcceptanceRepo(),
        tenant_repository=tenant_repo or FakeTenantRepo(tenant),
        auth_service=auth_service or FakeAuthService(_tokens()),
        oidc_client_factory=oidc_factory,
    )


def _build_config(
    tenant_id: UUID | None,
    *,
    provider_key: str = "google",
    policy: SsoAutoProvisionPolicy = SsoAutoProvisionPolicy.INVITE_ONLY,
    allowed_domains: list[str] | None = None,
    client_id: str = "client-id",
    enabled: bool = True,
) -> SsoProviderConfig:
    now = datetime.now(UTC)
    return SsoProviderConfig(
        id=uuid4(),
        tenant_id=tenant_id,
        provider_key=provider_key,
        enabled=enabled,
        issuer_url="https://accounts.google.com",
        client_id=client_id,
        client_secret="secret",
        discovery_url=None,
        scopes=["openid", "email", "profile"],
        pkce_required=True,
        token_endpoint_auth_method=SsoTokenAuthMethod.CLIENT_SECRET_POST,
        allowed_id_token_algs=[],
        auto_provision_policy=policy,
        allowed_domains=allowed_domains or [],
        default_role=TenantRole.MEMBER,
        created_at=now,
        updated_at=now,
    )


def _build_tenant() -> TenantAccount:
    now = datetime.now(UTC)
    return TenantAccount(
        id=uuid4(),
        slug="acme",
        name="Acme",
        status=TenantAccountStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


def _build_user(email: str, *, user_id: UUID | None = None) -> UserRecord:
    now = datetime.now(UTC)
    return UserRecord(
        id=user_id or uuid4(),
        email=email,
        status=UserStatus.ACTIVE,
        password_hash="hash",
        password_pepper_version="v2",
        created_at=now,
        updated_at=now,
        display_name=None,
        given_name=None,
        family_name=None,
        avatar_url=None,
        timezone=None,
        locale=None,
        memberships=[],
        email_verified_at=None,
        platform_role=None,
    )


def _build_invite(*, tenant_id: UUID, token_hash: str) -> TeamInvite:
    now = datetime.now(UTC)
    return TeamInvite(
        id=uuid4(),
        tenant_id=tenant_id,
        token_hash=token_hash,
        token_hint="hint",
        invited_email="owner@example.com",
        role=TenantRole.MEMBER,
        status=TeamInviteStatus.ACTIVE,
        created_by_user_id=None,
        accepted_by_user_id=None,
        accepted_at=None,
        revoked_at=None,
        revoked_reason=None,
        expires_at=None,
        created_at=now,
        updated_at=now,
    )


def _discovery(config: SsoProviderConfig) -> OidcDiscoveryDocument:
    return OidcDiscoveryDocument(
        issuer=config.issuer_url,
        authorization_endpoint="https://auth.example.com/authorize",
        token_endpoint="https://auth.example.com/token",
        jwks_uri="https://auth.example.com/jwks",
        id_token_signing_alg_values_supported=["RS256"],
        token_endpoint_auth_methods_supported=["client_secret_post", "client_secret_basic"],
    )


def _tokens() -> UserSessionTokens:
    now = datetime.now(UTC)
    return UserSessionTokens(
        access_token="access",
        refresh_token="refresh",
        expires_at=now,
        refresh_expires_at=now,
        kid="kid",
        refresh_kid="kid",
        scopes=["scope"],
        tenant_id=str(uuid4()),
        user_id=str(uuid4()),
        email_verified=True,
        session_id=str(uuid4()),
    )
