"""OIDC SSO orchestration service."""

from __future__ import annotations

import base64
import hashlib
import secrets
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from app.core.security import PASSWORD_HASH_VERSION, get_password_hash
from app.core.settings import Settings, get_settings
from app.domain.sso import (
    SsoAutoProvisionPolicy,
    SsoProviderConfig,
    SsoProviderConfigRepository,
    SsoTokenAuthMethod,
    UserIdentityRepository,
    UserIdentityUpsert,
)
from app.domain.team import (
    TeamInviteAcceptanceRepository,
    TeamInviteRepository,
    TeamInviteStatus,
    TenantMembershipRepository,
)
from app.domain.team_errors import (
    TeamInviteEmailMismatchError,
    TeamInviteExpiredError,
    TeamInviteNotFoundError,
    TeamInviteRevokedError,
    TeamInviteUserExistsError,
    TeamInviteValidationError,
    TeamMemberAlreadyExistsError,
)
from app.domain.tenant_accounts import TenantAccount, TenantAccountRepository
from app.domain.tenant_roles import TenantRole
from app.domain.users import (
    UserCreatePayload,
    UserProfilePatch,
    UserRecord,
    UserRepository,
    UserRepositoryError,
    UserStatus,
)
from app.infrastructure.persistence.auth.membership_repository import (
    get_tenant_membership_repository,
)
from app.infrastructure.persistence.auth.sso_repository import (
    get_sso_provider_config_repository,
    get_user_identity_repository,
)
from app.infrastructure.persistence.auth.team_invite_acceptance_repository import (
    get_team_invite_acceptance_repository,
)
from app.infrastructure.persistence.auth.team_invite_repository import get_team_invite_repository
from app.infrastructure.persistence.auth.user_repository import get_user_repository
from app.infrastructure.persistence.tenants.account_repository import (
    get_tenant_account_repository,
)
from app.observability.logging import log_event
from app.services.auth.errors import MfaRequiredError, UserAuthenticationError
from app.services.auth_service import AuthService, UserSessionTokens, get_auth_service
from app.services.sso.oidc_client import (
    OidcClient,
    OidcDiscoveryDocument,
    OidcDiscoveryError,
    OidcError,
    OidcTokenExchangeError,
    OidcTokenVerificationError,
)
from app.services.sso.state_store import SsoStatePayload, SsoStateStore, build_sso_state_store

_DEFAULT_SCOPES = ["openid", "email", "profile"]
_SAFE_ID_TOKEN_ALGS = {
    "RS256",
    "RS384",
    "RS512",
    "PS256",
    "PS384",
    "PS512",
    "ES256",
    "ES384",
    "ES512",
}


class SsoServiceError(RuntimeError):
    """Base class for SSO service errors."""

    def __init__(self, message: str, *, reason: str | None = None) -> None:
        super().__init__(message)
        self.reason = reason


class SsoConfigurationError(SsoServiceError):
    """Raised when SSO is not configured or disabled for a tenant."""


class SsoStateError(SsoServiceError):
    """Raised when SSO state or nonce validation fails."""


class SsoTokenError(SsoServiceError):
    """Raised when token exchange or verification fails."""


class SsoIdentityError(SsoServiceError):
    """Raised when identity linkage fails or conflicts."""


class SsoProvisioningError(SsoServiceError):
    """Raised when auto-provisioning rules block the login."""


@dataclass(slots=True)
class SsoStartResult:
    authorize_url: str
    state: str


class SsoService:
    """Coordinates OIDC SSO flows and user provisioning policies."""

    def __init__(
        self,
        *,
        settings_factory: Callable[[], Settings] | None = None,
        state_store: SsoStateStore | None = None,
        provider_repository: SsoProviderConfigRepository | None = None,
        identity_repository: UserIdentityRepository | None = None,
        user_repository: UserRepository | None = None,
        membership_repository: TenantMembershipRepository | None = None,
        invite_repository: TeamInviteRepository | None = None,
        invite_acceptance_repository: TeamInviteAcceptanceRepository | None = None,
        tenant_repository: TenantAccountRepository | None = None,
        auth_service: AuthService | None = None,
        oidc_client_factory: Callable[[], OidcClient] | None = None,
    ) -> None:
        self._settings_factory = settings_factory or get_settings
        self._state_store = state_store
        self._provider_repository = provider_repository
        self._identity_repository = identity_repository
        self._user_repository = user_repository
        self._membership_repository = membership_repository
        self._invite_repository = invite_repository
        self._invite_acceptance_repository = invite_acceptance_repository
        self._tenant_repository = tenant_repository
        self._auth_service = auth_service
        self._oidc_client_factory = oidc_client_factory or OidcClient

    def _get_settings(self) -> Settings:
        return self._settings_factory()

    def _get_state_store(self) -> SsoStateStore:
        if self._state_store is None:
            self._state_store = build_sso_state_store(self._get_settings())
        return self._state_store

    def _get_provider_repository(self) -> SsoProviderConfigRepository:
        if self._provider_repository is None:
            self._provider_repository = get_sso_provider_config_repository(self._get_settings())
        if self._provider_repository is None:
            raise RuntimeError("SSO provider config repository is not configured.")
        return self._provider_repository

    def _get_identity_repository(self) -> UserIdentityRepository:
        if self._identity_repository is None:
            self._identity_repository = get_user_identity_repository(self._get_settings())
        if self._identity_repository is None:
            raise RuntimeError("User identity repository is not configured.")
        return self._identity_repository

    def _get_user_repository(self) -> UserRepository:
        if self._user_repository is None:
            self._user_repository = get_user_repository(self._get_settings())
        if self._user_repository is None:
            raise RuntimeError("User repository is not configured.")
        return self._user_repository

    def _get_membership_repository(self) -> TenantMembershipRepository:
        if self._membership_repository is None:
            self._membership_repository = get_tenant_membership_repository(self._get_settings())
        if self._membership_repository is None:
            raise RuntimeError("Tenant membership repository is not configured.")
        return self._membership_repository

    def _get_invite_repository(self) -> TeamInviteRepository:
        if self._invite_repository is None:
            self._invite_repository = get_team_invite_repository(self._get_settings())
        if self._invite_repository is None:
            raise RuntimeError("Team invite repository is not configured.")
        return self._invite_repository

    def _get_invite_acceptance_repository(self) -> TeamInviteAcceptanceRepository:
        if self._invite_acceptance_repository is None:
            self._invite_acceptance_repository = get_team_invite_acceptance_repository(
                self._get_settings()
            )
        if self._invite_acceptance_repository is None:
            raise RuntimeError("Team invite acceptance repository is not configured.")
        return self._invite_acceptance_repository

    def _get_tenant_repository(self) -> TenantAccountRepository:
        if self._tenant_repository is None:
            self._tenant_repository = get_tenant_account_repository(self._get_settings())
        if self._tenant_repository is None:
            raise RuntimeError("Tenant account repository is not configured.")
        return self._tenant_repository

    def _get_auth_service(self) -> AuthService:
        if self._auth_service is None:
            self._auth_service = get_auth_service()
        return self._auth_service

    async def start_sso(
        self,
        *,
        provider_key: str,
        tenant_id: UUID | str | None,
        tenant_slug: str | None,
        redirect_uri: str | None = None,
        login_hint: str | None = None,
    ) -> SsoStartResult:
        try:
            normalized_provider = _normalize_provider_key(provider_key)
        except SsoServiceError as exc:
            _log_sso_event(
                "auth.sso.start",
                result="failure",
                reason=exc.reason or "unknown",
                provider=provider_key or None,
                tenant_slug=tenant_slug,
                detail=str(exc),
            )
            raise

        tenant: TenantAccount | None = None
        try:
            tenant = await self._resolve_tenant(
                tenant_id=tenant_id,
                tenant_slug=tenant_slug,
            )
            config = await self._load_provider_config(
                tenant_id=tenant.id, provider_key=normalized_provider
            )
            if not config.enabled:
                raise SsoConfigurationError(
                    "SSO provider is disabled.",
                    reason="provider_disabled",
                )

            resolved_redirect_uri = redirect_uri or _default_redirect_uri(
                self._get_settings(), provider_key=normalized_provider
            )
            scopes = _resolve_scopes(config.scopes)

            state = _generate_state()
            nonce = _generate_nonce()
            pkce_verifier = _generate_pkce_verifier() if config.pkce_required else None
            await self._get_state_store().set_state(
                state,
                SsoStatePayload(
                    tenant_id=str(tenant.id),
                    provider_key=normalized_provider,
                    pkce_verifier=pkce_verifier,
                    nonce=nonce,
                    redirect_uri=resolved_redirect_uri,
                    scopes=scopes,
                ),
            )

            oidc_client = self._oidc_client_factory()
            try:
                discovery = await oidc_client.fetch_discovery(
                    config.issuer_url, discovery_url=config.discovery_url
                )
            except OidcError as exc:
                raise SsoConfigurationError(
                    "Failed to load provider discovery metadata.",
                    reason="discovery_failed",
                ) from exc
            finally:
                await oidc_client.close()

            authorize_url = _build_authorize_url(
                discovery.authorization_endpoint,
                client_id=config.client_id,
                redirect_uri=resolved_redirect_uri,
                scopes=scopes,
                state=state,
                nonce=nonce,
                code_challenge=_code_challenge(pkce_verifier) if pkce_verifier else None,
                login_hint=login_hint,
            )

            log_event(
                "auth.sso.start",
                result="success",
                provider=normalized_provider,
                tenant_id=str(tenant.id),
                issuer=config.issuer_url,
            )

            return SsoStartResult(authorize_url=authorize_url, state=state)
        except SsoServiceError as exc:
            _log_sso_event(
                "auth.sso.start",
                result="failure",
                reason=exc.reason or "unknown",
                provider=normalized_provider,
                tenant_id=str(tenant.id) if tenant else None,
                tenant_slug=tenant_slug,
                detail=str(exc),
            )
            raise

    async def complete_sso(
        self,
        *,
        provider_key: str,
        code: str,
        state: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserSessionTokens:
        try:
            normalized_provider = _normalize_provider_key(provider_key)
        except SsoServiceError as exc:
            _log_sso_event(
                "auth.sso.callback",
                result="failure",
                reason=exc.reason or "unknown",
                provider=provider_key or None,
                detail=str(exc),
            )
            raise

        tenant_id: UUID | None = None
        user_id: UUID | None = None
        try:
            state_payload = await self._get_state_store().consume_state(state)
            if state_payload is None:
                raise SsoStateError(
                    "SSO state is invalid or expired.",
                    reason="state_invalid",
                )
            if state_payload.provider_key != normalized_provider:
                raise SsoStateError("SSO provider mismatch.", reason="provider_mismatch")

            tenant_id = _parse_uuid(state_payload.tenant_id)
            config = await self._load_provider_config(
                tenant_id=tenant_id,
                provider_key=normalized_provider,
            )
            if not config.enabled:
                raise SsoConfigurationError(
                    "SSO provider is disabled.",
                    reason="provider_disabled",
                )

            oidc_client = self._oidc_client_factory()
            discovery = None
            try:
                discovery = await oidc_client.fetch_discovery(
                    config.issuer_url, discovery_url=config.discovery_url
                )
                token_auth_method = _resolve_token_auth_method(config, discovery)
                if config.pkce_required and not state_payload.pkce_verifier:
                    raise SsoStateError(
                        "SSO PKCE verifier missing.",
                        reason="pkce_missing",
                    )
                token_response = await oidc_client.exchange_code_for_tokens(
                    token_endpoint=discovery.token_endpoint,
                    client_id=config.client_id,
                    client_secret=config.client_secret,
                    code=code,
                    redirect_uri=state_payload.redirect_uri,
                    code_verifier=state_payload.pkce_verifier,
                    token_auth_method=token_auth_method.value,
                )
                allowed_algs = _resolve_allowed_id_token_algs(config, discovery)
                claims = await oidc_client.verify_id_token(
                    id_token=token_response.id_token,
                    issuer=discovery.issuer,
                    audience=config.client_id,
                    jwks_uri=discovery.jwks_uri,
                    allowed_algs=allowed_algs,
                    clock_skew_seconds=int(self._get_settings().sso_clock_skew_seconds),
                )
            except OidcDiscoveryError as exc:
                raise SsoTokenError(
                    "SSO discovery failed.",
                    reason="discovery_failed",
                ) from exc
            except OidcTokenExchangeError as exc:
                raise SsoTokenError(
                    "SSO token exchange failed.",
                    reason="token_exchange_failed",
                ) from exc
            except OidcTokenVerificationError as exc:
                raise SsoTokenError(
                    "SSO token validation failed.",
                    reason="token_verification_failed",
                ) from exc
            except OidcError as exc:
                raise SsoTokenError(
                    "SSO token handling failed.",
                    reason="token_handling_failed",
                ) from exc
            finally:
                await oidc_client.close()

            if discovery is None:
                raise SsoTokenError(
                    "SSO discovery metadata was unavailable.",
                    reason="discovery_missing",
                )

            _validate_nonce(claims, expected=state_payload.nonce)

            subject = _require_claim(claims, "sub")
            issuer = str(claims.get("iss") or discovery.issuer)
            email = _normalize_email(_optional_str_claim(claims, "email"))
            email_verified = _parse_bool_claim(claims.get("email_verified"))

            user = await self._resolve_user(
                provider_key=normalized_provider,
                issuer=issuer,
                subject=subject,
                email=email,
                email_verified=email_verified,
            )

            user = await self._ensure_membership(
                user=user,
                tenant_id=tenant_id,
                policy=config.auto_provision_policy,
                allowed_domains=config.allowed_domains,
                default_role=config.default_role,
                email=email,
                email_verified=email_verified,
                display_name=_optional_str_claim(claims, "name"),
            )

            user_id = user.id
            now = datetime.now(UTC)
            if email_verified and user.email_verified_at is None:
                await self._get_user_repository().mark_email_verified(user.id, timestamp=now)

            profile_update, provided_fields = _profile_patch_from_claims(claims)
            if provided_fields:
                await self._get_user_repository().upsert_user_profile(
                    user.id,
                    profile_update,
                    provided_fields=provided_fields,
                )

            try:
                identity = await self._get_identity_repository().upsert(
                    UserIdentityUpsert(
                        user_id=user.id,
                        provider_key=normalized_provider,
                        issuer=issuer,
                        subject=subject,
                        email=email,
                        email_verified=email_verified,
                        profile=_identity_profile_from_claims(claims),
                        linked_at=now,
                        last_login_at=now,
                    )
                )
            except RuntimeError as exc:
                raise SsoIdentityError(
                    "Failed to link SSO identity.",
                    reason="identity_link_failed",
                ) from exc

            log_event(
                "auth.sso.linked",
                result="success",
                provider=normalized_provider,
                tenant_id=str(tenant_id),
                user_id=str(user.id),
                identity_id=str(identity.id),
            )

            tokens = await self._get_auth_service().issue_user_session(
                user_id=user.id,
                tenant_id=tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                reason="sso",
                enforce_mfa=True,
            )

            log_event(
                "auth.sso.callback",
                result="success",
                provider=normalized_provider,
                tenant_id=str(tenant_id),
                user_id=str(user.id),
            )
            return tokens
        except MfaRequiredError:
            _log_sso_event(
                "auth.sso.callback",
                result="mfa_required",
                reason="mfa_required",
                provider=normalized_provider,
                tenant_id=tenant_id,
                user_id=user_id,
            )
            raise
        except UserAuthenticationError as exc:
            _log_sso_event(
                "auth.sso.callback",
                result="failure",
                reason="auth_failed",
                provider=normalized_provider,
                tenant_id=tenant_id,
                user_id=user_id,
                detail=str(exc),
            )
            raise
        except SsoServiceError as exc:
            _log_sso_event(
                "auth.sso.callback",
                result="failure",
                reason=exc.reason or "unknown",
                provider=normalized_provider,
                tenant_id=tenant_id,
                user_id=user_id,
                detail=str(exc),
            )
            raise

    async def list_providers(
        self,
        *,
        tenant_id: UUID | str | None,
        tenant_slug: str | None,
    ) -> list[SsoProviderConfig]:
        tenant = await self._resolve_tenant(tenant_id=tenant_id, tenant_slug=tenant_slug)
        provider_repo = self._get_provider_repository()
        try:
            tenant_configs = await provider_repo.list_for_tenant(tenant_id=tenant.id)
            global_configs = await provider_repo.list_for_tenant(tenant_id=None)
        except ValueError as exc:
            raise SsoConfigurationError(
                "SSO provider configuration is invalid.",
                reason="provider_config_invalid",
            ) from exc
        global_configs = [config for config in global_configs if config.enabled]

        by_key: dict[str, SsoProviderConfig] = {
            config.provider_key: config for config in global_configs
        }
        for config in tenant_configs:
            if config.enabled:
                by_key[config.provider_key] = config
            else:
                by_key.pop(config.provider_key, None)

        return sorted(by_key.values(), key=lambda item: item.provider_key)

    async def _resolve_tenant(
        self, *, tenant_id: UUID | str | None, tenant_slug: str | None
    ) -> TenantAccount:
        if tenant_id:
            resolved_id = _parse_uuid(tenant_id)
            record = await self._get_tenant_repository().get(resolved_id)
        elif tenant_slug:
            record = await self._get_tenant_repository().get_by_slug(tenant_slug)
        else:
            record = None

        if record is None:
            reason = "tenant_required" if not tenant_id and not tenant_slug else "tenant_not_found"
            raise SsoConfigurationError(
                "Tenant context is required for SSO.",
                reason=reason,
            )
        return record

    async def _load_provider_config(
        self, *, tenant_id: UUID, provider_key: str
    ) -> SsoProviderConfig:
        try:
            config = await self._get_provider_repository().fetch_with_fallback(
                tenant_id=tenant_id, provider_key=provider_key
            )
        except ValueError as exc:
            raise SsoConfigurationError(
                "SSO provider configuration is invalid.",
                reason="provider_config_invalid",
            ) from exc
        if config is None:
            raise SsoConfigurationError(
                "SSO provider is not configured for this tenant.",
                reason="provider_not_configured",
            )
        return config

    async def _resolve_user(
        self,
        *,
        provider_key: str,
        issuer: str,
        subject: str,
        email: str | None,
        email_verified: bool,
    ) -> UserRecord | None:
        identity_repo = self._get_identity_repository()
        user_repo = self._get_user_repository()

        identity = await identity_repo.get_by_subject(
            provider_key=provider_key,
            issuer=issuer,
            subject=subject,
        )
        user: UserRecord | None = None

        if identity is not None:
            user = await user_repo.get_user_by_id(identity.user_id)
            if user is None:
                raise SsoIdentityError(
                    "SSO identity references an unknown user.",
                    reason="identity_orphaned",
                )

        if user is None and email and email_verified:
            user = await user_repo.get_user_by_email(email)

        if user is not None:
            existing_identity = await identity_repo.get_by_user(
                user_id=user.id,
                provider_key=provider_key,
            )
            if existing_identity and (
                existing_identity.subject != subject or existing_identity.issuer != issuer
            ):
                raise SsoIdentityError(
                    "This provider is already linked to a different identity for the user.",
                    reason="identity_conflict",
                )
        return user

    async def _ensure_membership(
        self,
        *,
        user: UserRecord | None,
        tenant_id: UUID,
        policy: SsoAutoProvisionPolicy,
        allowed_domains: list[str],
        default_role: TenantRole,
        email: str | None,
        email_verified: bool,
        display_name: str | None,
    ) -> UserRecord:
        membership_repo = self._get_membership_repository()
        if user is not None and await membership_repo.membership_exists(
            tenant_id=tenant_id, user_id=user.id
        ):
            return user

        if policy == SsoAutoProvisionPolicy.DISABLED:
            raise SsoProvisioningError(
                "SSO access is restricted to existing members.",
                reason="policy_disabled",
            )

        if not email or not email_verified:
            raise SsoProvisioningError(
                "Verified email is required for SSO provisioning.",
                reason="email_unverified",
            )

        if policy == SsoAutoProvisionPolicy.INVITE_ONLY:
            return await self._accept_invite(
                tenant_id=tenant_id,
                user=user,
                email=email,
                display_name=display_name,
            )

        if policy == SsoAutoProvisionPolicy.DOMAIN_ALLOWLIST:
            if not _email_domain_allowed(email, allowed_domains):
                raise SsoProvisioningError(
                    "Email domain is not allowed for SSO provisioning.",
                    reason="domain_not_allowed",
                )
            if user is None:
                return await self._create_user_with_membership(
                    tenant_id=tenant_id,
                    email=email,
                    default_role=default_role,
                    display_name=display_name,
                )
            try:
                await membership_repo.add_member(
                    tenant_id=tenant_id,
                    user_id=user.id,
                    role=default_role,
                )
            except TeamMemberAlreadyExistsError:
                pass
            log_event(
                "auth.sso.provisioned",
                result="success",
                policy="domain_allowlist",
                tenant_id=str(tenant_id),
                user_id=str(user.id),
            )
            return user

        raise SsoProvisioningError(
            "Unsupported SSO provisioning policy.",
            reason="policy_unsupported",
        )

    async def _accept_invite(
        self,
        *,
        tenant_id: UUID,
        user: UserRecord | None,
        email: str,
        display_name: str | None,
    ) -> UserRecord:
        invite_repo = self._get_invite_repository()
        acceptance_repo = self._get_invite_acceptance_repository()
        now = datetime.now(UTC)

        invites = await invite_repo.list_invites(
            tenant_id=tenant_id,
            status=TeamInviteStatus.ACTIVE,
            email=email,
            limit=5,
            offset=0,
        )
        if not invites.invites:
            raise SsoProvisioningError(
                "An active invite is required for SSO.",
                reason="invite_required",
            )

        last_error: Exception | None = None
        for invite in invites.invites:
            try:
                if user:
                    try:
                        await acceptance_repo.accept_for_existing_user(
                            token_hash=invite.token_hash,
                            user_id=user.id,
                            now=now,
                        )
                    except TeamMemberAlreadyExistsError:
                        await invite_repo.mark_accepted(
                            invite.id,
                            timestamp=now,
                            accepted_by_user_id=user.id,
                        )
                    await self._get_user_repository().mark_email_verified(user.id, timestamp=now)
                    log_event(
                        "auth.sso.provisioned",
                        result="success",
                        policy="invite_only",
                        tenant_id=str(tenant_id),
                        user_id=str(user.id),
                    )
                    return user

                password_seed = secrets.token_urlsafe(32)
                result = await acceptance_repo.accept_for_new_user(
                    token_hash=invite.token_hash,
                    password_hash=get_password_hash(password_seed),
                    password_pepper_version=PASSWORD_HASH_VERSION,
                    display_name=display_name,
                    now=now,
                )
                created = await self._get_user_repository().get_user_by_id(result.user_id)
                if created is None:
                    raise SsoProvisioningError(
                        "Failed to load provisioned user.",
                        reason="provisioning_failed",
                    )
                log_event(
                    "auth.sso.provisioned",
                    result="success",
                    policy="invite_only",
                    tenant_id=str(tenant_id),
                    user_id=str(created.id),
                )
                return created
            except (
                TeamInviteExpiredError,
                TeamInviteNotFoundError,
                TeamInviteRevokedError,
                TeamInviteEmailMismatchError,
                TeamInviteUserExistsError,
                TeamInviteValidationError,
            ) as exc:
                last_error = exc
                continue

        if last_error:
            raise SsoProvisioningError(
                "Invite validation failed for SSO provisioning.",
                reason="invite_invalid",
            ) from last_error
        raise SsoProvisioningError(
            "An active invite is required for SSO.",
            reason="invite_required",
        )

    async def _create_user_with_membership(
        self,
        *,
        tenant_id: UUID,
        email: str,
        default_role: TenantRole,
        display_name: str | None,
    ) -> UserRecord:
        password_seed = secrets.token_urlsafe(32)
        payload = UserCreatePayload(
            email=email,
            password_hash=get_password_hash(password_seed),
            password_pepper_version=PASSWORD_HASH_VERSION,
            status=UserStatus.ACTIVE,
            tenant_id=tenant_id,
            role=default_role,
            display_name=display_name,
        )
        user_repo = self._get_user_repository()
        membership_repo = self._get_membership_repository()
        try:
            user = await user_repo.create_user(payload)
        except UserRepositoryError as exc:
            existing = await user_repo.get_user_by_email(email)
            if existing is None:
                raise SsoProvisioningError(
                    "Failed to provision user.",
                    reason="provisioning_failed",
                ) from exc
            try:
                await membership_repo.add_member(
                    tenant_id=tenant_id,
                    user_id=existing.id,
                    role=default_role,
                )
            except TeamMemberAlreadyExistsError:
                pass
            log_event(
                "auth.sso.provisioned",
                result="success",
                policy="domain_allowlist",
                tenant_id=str(tenant_id),
                user_id=str(existing.id),
            )
            return existing

        await user_repo.mark_email_verified(user.id, timestamp=datetime.now(UTC))
        log_event(
            "auth.sso.provisioned",
            result="success",
            policy="domain_allowlist",
            tenant_id=str(tenant_id),
            user_id=str(user.id),
        )
        return user


def build_sso_service(
    *,
    settings: Settings | None = None,
    state_store: SsoStateStore | None = None,
    provider_repository: SsoProviderConfigRepository | None = None,
    identity_repository: UserIdentityRepository | None = None,
    user_repository: UserRepository | None = None,
    membership_repository: TenantMembershipRepository | None = None,
    invite_repository: TeamInviteRepository | None = None,
    invite_acceptance_repository: TeamInviteAcceptanceRepository | None = None,
    tenant_repository: TenantAccountRepository | None = None,
    auth_service: AuthService | None = None,
    oidc_client_factory: Callable[[], OidcClient] | None = None,
) -> SsoService:
    resolved_settings = settings or get_settings()

    resolved_state_store = state_store or build_sso_state_store(resolved_settings)
    resolved_provider_repo = (
        provider_repository or get_sso_provider_config_repository(resolved_settings)
    )
    resolved_identity_repo = (
        identity_repository or get_user_identity_repository(resolved_settings)
    )
    resolved_user_repo = user_repository or get_user_repository(resolved_settings)
    resolved_membership_repo = (
        membership_repository or get_tenant_membership_repository(resolved_settings)
    )
    resolved_invite_repo = invite_repository or get_team_invite_repository(resolved_settings)
    resolved_invite_acceptance_repo = (
        invite_acceptance_repository
        or get_team_invite_acceptance_repository(resolved_settings)
    )
    resolved_tenant_repo = tenant_repository or get_tenant_account_repository(resolved_settings)
    resolved_auth_service = auth_service or get_auth_service()

    if resolved_provider_repo is None:
        raise RuntimeError("SSO provider config repository is not configured.")
    if resolved_identity_repo is None:
        raise RuntimeError("User identity repository is not configured.")
    if resolved_user_repo is None:
        raise RuntimeError("User repository is not configured.")
    if resolved_membership_repo is None:
        raise RuntimeError("Tenant membership repository is not configured.")
    if resolved_invite_repo is None:
        raise RuntimeError("Team invite repository is not configured.")
    if resolved_invite_acceptance_repo is None:
        raise RuntimeError("Team invite acceptance repository is not configured.")
    if resolved_tenant_repo is None:
        raise RuntimeError("Tenant account repository is not configured.")

    return SsoService(
        settings_factory=lambda: resolved_settings,
        state_store=resolved_state_store,
        provider_repository=resolved_provider_repo,
        identity_repository=resolved_identity_repo,
        user_repository=resolved_user_repo,
        membership_repository=resolved_membership_repo,
        invite_repository=resolved_invite_repo,
        invite_acceptance_repository=resolved_invite_acceptance_repo,
        tenant_repository=resolved_tenant_repo,
        auth_service=resolved_auth_service,
        oidc_client_factory=oidc_client_factory,
    )


def get_sso_service() -> SsoService:
    from app.bootstrap.container import get_container

    container = get_container()
    if container.sso_service is None:
        container.sso_service = build_sso_service()
    assert container.sso_service is not None
    return container.sso_service


def _normalize_provider_key(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        raise SsoConfigurationError(
            "SSO provider key is required.",
            reason="provider_required",
        )
    return normalized


def _parse_uuid(value: UUID | str | None) -> UUID:
    if value is None:
        raise SsoConfigurationError(
            "Tenant identifier is required.",
            reason="tenant_required",
        )
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise SsoConfigurationError(
            "Tenant identifier is invalid.",
            reason="tenant_invalid",
        ) from exc


def _normalize_email(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    return normalized or None


def _resolve_scopes(scopes: list[str]) -> list[str]:
    resolved = [scope.strip() for scope in scopes if scope and scope.strip()]
    if not resolved:
        resolved = list(_DEFAULT_SCOPES)
    if "openid" not in resolved:
        resolved.insert(0, "openid")
    return resolved


def _generate_state() -> str:
    return secrets.token_urlsafe(32)


def _generate_nonce() -> str:
    return secrets.token_urlsafe(24)


def _generate_pkce_verifier() -> str:
    raw = secrets.token_bytes(32)
    return _urlsafe_b64(raw)


def _code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return _urlsafe_b64(digest)


def _urlsafe_b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _build_authorize_url(
    base_url: str,
    *,
    client_id: str,
    redirect_uri: str,
    scopes: list[str],
    state: str,
    nonce: str,
    code_challenge: str | None,
    login_hint: str | None,
) -> str:
    params: dict[str, str] = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state,
        "nonce": nonce,
    }
    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"
    if login_hint:
        params["login_hint"] = login_hint
    return f"{base_url}?{urlencode(params)}"


def _default_redirect_uri(settings: Settings, *, provider_key: str) -> str:
    base = (settings.app_public_url or "http://localhost:3000").strip().rstrip("/")
    return f"{base}/auth/sso/{provider_key}/callback"


def _resolve_token_auth_method(
    config: SsoProviderConfig, discovery: OidcDiscoveryDocument
) -> SsoTokenAuthMethod:
    method = config.token_endpoint_auth_method
    supported = getattr(discovery, "token_endpoint_auth_methods_supported", None)
    if supported:
        normalized_supported = {
            str(item).strip().lower() for item in supported if str(item).strip()
        }
        if method.value not in normalized_supported:
            raise SsoConfigurationError(
                "Token endpoint auth method is not supported by provider.",
                reason="token_auth_method_unsupported",
            )
    if method in {
        SsoTokenAuthMethod.CLIENT_SECRET_BASIC,
        SsoTokenAuthMethod.CLIENT_SECRET_POST,
    } and not config.client_secret:
        raise SsoConfigurationError(
            "Client secret is required for token endpoint authentication.",
            reason="client_secret_required",
        )
    if method == SsoTokenAuthMethod.NONE and not config.pkce_required:
        raise SsoConfigurationError(
            "Public clients must require PKCE.",
            reason="pkce_required_for_public_client",
        )
    return method


def _normalize_alg_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    normalized: list[str] = []
    for value in values:
        if not value:
            continue
        alg = str(value).strip().upper()
        if alg:
            normalized.append(alg)
    return normalized


def _resolve_allowed_id_token_algs(
    config: SsoProviderConfig, discovery: OidcDiscoveryDocument
) -> list[str]:
    configured = _normalize_alg_list(config.allowed_id_token_algs)
    supported_raw = getattr(discovery, "id_token_signing_alg_values_supported", None)
    supported = _normalize_alg_list(list(supported_raw) if supported_raw else [])

    if configured:
        configured = [alg for alg in configured if alg in _SAFE_ID_TOKEN_ALGS]
        if not configured:
            raise SsoConfigurationError(
                "Allowed ID token algorithms are invalid.",
                reason="id_token_alg_invalid",
            )
        if supported:
            unsupported = [alg for alg in configured if alg not in supported]
            if unsupported:
                raise SsoConfigurationError(
                    "Allowed ID token algorithms are not supported by provider.",
                    reason="id_token_alg_unsupported",
                )
        return configured

    if supported:
        allowed = [alg for alg in supported if alg in _SAFE_ID_TOKEN_ALGS]
        if not allowed:
            raise SsoConfigurationError(
                "Provider does not advertise supported asymmetric ID token algorithms.",
                reason="id_token_alg_unsupported",
            )
        return allowed

    return ["RS256"]


def _log_sso_event(
    event: str,
    *,
    result: str,
    reason: str | None = None,
    provider: str | None = None,
    tenant_id: UUID | str | None = None,
    tenant_slug: str | None = None,
    user_id: UUID | str | None = None,
    detail: str | None = None,
) -> None:
    fields: dict[str, Any] = {"result": result}
    if reason:
        fields["reason"] = reason
    if provider:
        fields["provider"] = provider
    if tenant_id:
        fields["tenant_id"] = str(tenant_id)
    if tenant_slug:
        fields["tenant_slug"] = tenant_slug
    if user_id:
        fields["user_id"] = str(user_id)
    if detail:
        fields["detail"] = detail
    log_event(event, **fields)


def _validate_nonce(claims: Mapping[str, Any], *, expected: str) -> None:
    nonce = claims.get("nonce")
    if not isinstance(nonce, str) or nonce != expected:
        raise SsoStateError(
            "SSO nonce validation failed.",
            reason="nonce_mismatch",
        )


def _require_claim(claims: Mapping[str, Any], key: str) -> str:
    value = claims.get(key)
    if not isinstance(value, str) or not value:
        raise SsoTokenError(
            f"OIDC token missing required claim: {key}.",
            reason=f"missing_claim:{key}",
        )
    return value


def _optional_str_claim(claims: Mapping[str, Any], key: str) -> str | None:
    value = claims.get(key)
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


def _parse_bool_claim(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    if isinstance(value, int):
        return value != 0
    return False


def _email_domain_allowed(email: str, allowlist: list[str]) -> bool:
    if not allowlist:
        return False
    domain = email.split("@")[-1].lower()
    for allowed in allowlist:
        normalized = allowed.strip().lower().lstrip("@")
        if not normalized:
            continue
        if domain == normalized:
            return True
        if domain.endswith(f".{normalized}"):
            return True
    return False


def _profile_patch_from_claims(
    claims: Mapping[str, Any],
) -> tuple[UserProfilePatch, set[str]]:
    update = UserProfilePatch(
        display_name=_optional_str_claim(claims, "name"),
        given_name=_optional_str_claim(claims, "given_name"),
        family_name=_optional_str_claim(claims, "family_name"),
        avatar_url=_optional_str_claim(claims, "picture"),
        locale=_optional_str_claim(claims, "locale"),
    )
    provided_fields = {
        field for field, value in asdict(update).items() if value is not None
    }
    return update, provided_fields


def _identity_profile_from_claims(claims: Mapping[str, Any]) -> dict[str, Any]:
    profile: dict[str, Any] = {}
    for key in ("name", "given_name", "family_name", "picture", "locale", "hd"):
        value = claims.get(key)
        if value is not None:
            profile[key] = value
    return profile


__all__ = [
    "SsoConfigurationError",
    "SsoIdentityError",
    "SsoProvisioningError",
    "SsoService",
    "SsoServiceError",
    "SsoStartResult",
    "SsoStateError",
    "SsoTokenError",
    "build_sso_service",
    "get_sso_service",
]
