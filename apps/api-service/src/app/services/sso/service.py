"""OIDC SSO orchestration service."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.settings import Settings, get_settings
from app.domain.sso import (
    SsoProviderConfig,
    SsoProviderConfigRepository,
    UserIdentityRepository,
    UserIdentityUpsert,
)
from app.domain.tenant_accounts import TenantAccount, TenantAccountRepository
from app.domain.users import UserRecord, UserRepository
from app.observability.logging import log_event
from app.services.auth.errors import MfaRequiredError, UserAuthenticationError
from app.services.auth_service import AuthService, UserSessionTokens, get_auth_service

from .claims import (
    identity_profile_from_claims,
    normalize_email,
    optional_str_claim,
    parse_bool_claim,
    profile_patch_from_claims,
    require_claim,
)
from .config import (
    build_authorize_url,
    default_redirect_uri,
    normalize_provider_key,
    resolve_allowed_id_token_algs,
    resolve_scopes,
    resolve_token_auth_method,
)
from .errors import (
    SsoConfigurationError,
    SsoIdentityError,
    SsoServiceError,
    SsoStateError,
    SsoTokenError,
)
from .models import SsoStartResult
from .oidc_client import (
    OidcClient,
    OidcDiscoveryError,
    OidcError,
    OidcTokenExchangeError,
    OidcTokenVerificationError,
)
from .pkce import code_challenge, generate_nonce, generate_pkce_verifier, generate_state
from .provisioning import SsoProvisioner, SsoProvisioningInput
from .state_store import SsoStatePayload, SsoStateStore, build_sso_state_store
from .telemetry import log_sso_event


class SsoService:
    """Coordinates OIDC SSO flows and user provisioning policies."""

    def __init__(
        self,
        *,
        settings_factory: Callable[[], Settings] | None = None,
        state_store: SsoStateStore | None = None,
        provider_repository: SsoProviderConfigRepository,
        identity_repository: UserIdentityRepository,
        user_repository: UserRepository,
        tenant_repository: TenantAccountRepository,
        auth_service: AuthService | None = None,
        oidc_client_factory: Callable[[], OidcClient] | None = None,
        provisioner: SsoProvisioner,
    ) -> None:
        self._settings_factory = settings_factory or get_settings
        self._state_store = state_store
        self._provider_repository = provider_repository
        self._identity_repository = identity_repository
        self._user_repository = user_repository
        self._tenant_repository = tenant_repository
        self._auth_service = auth_service
        self._oidc_client_factory = oidc_client_factory or OidcClient
        self._provisioner = provisioner

    def _get_settings(self) -> Settings:
        return self._settings_factory()

    def _get_state_store(self) -> SsoStateStore:
        if self._state_store is None:
            self._state_store = build_sso_state_store(self._get_settings())
        return self._state_store

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
            normalized_provider = normalize_provider_key(provider_key)
        except SsoServiceError as exc:
            log_sso_event(
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

            resolved_redirect_uri = redirect_uri or default_redirect_uri(
                self._get_settings(), provider_key=normalized_provider
            )
            scopes = resolve_scopes(config.scopes)

            state = generate_state()
            nonce = generate_nonce()
            pkce_verifier = generate_pkce_verifier() if config.pkce_required else None
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

            authorize_url = build_authorize_url(
                discovery.authorization_endpoint,
                client_id=config.client_id,
                redirect_uri=resolved_redirect_uri,
                scopes=scopes,
                state=state,
                nonce=nonce,
                code_challenge=code_challenge(pkce_verifier) if pkce_verifier else None,
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
            log_sso_event(
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
            normalized_provider = normalize_provider_key(provider_key)
        except SsoServiceError as exc:
            log_sso_event(
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
                token_auth_method = resolve_token_auth_method(config, discovery)
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
                allowed_algs = resolve_allowed_id_token_algs(config, discovery)
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

            subject = require_claim(claims, "sub")
            issuer = str(claims.get("iss") or discovery.issuer)
            email = normalize_email(optional_str_claim(claims, "email"))
            email_verified = parse_bool_claim(claims.get("email_verified"))

            user = await self._resolve_user(
                provider_key=normalized_provider,
                issuer=issuer,
                subject=subject,
                email=email,
                email_verified=email_verified,
            )

            now = datetime.now(UTC)
            user = await self._provisioner.ensure_membership(
                payload=SsoProvisioningInput(
                    user=user,
                    tenant_id=tenant_id,
                    policy=config.auto_provision_policy,
                    allowed_domains=config.allowed_domains,
                    default_role=config.default_role,
                    email=email,
                    email_verified=email_verified,
                    display_name=optional_str_claim(claims, "name"),
                    now=now,
                )
            )

            user_id = user.id
            if email_verified and user.email_verified_at is None:
                await self._user_repository.mark_email_verified(user.id, timestamp=now)

            profile_update, provided_fields = profile_patch_from_claims(claims)
            if provided_fields:
                await self._user_repository.upsert_user_profile(
                    user.id,
                    profile_update,
                    provided_fields=provided_fields,
                )

            try:
                identity = await self._identity_repository.upsert(
                    UserIdentityUpsert(
                        user_id=user.id,
                        provider_key=normalized_provider,
                        issuer=issuer,
                        subject=subject,
                        email=email,
                        email_verified=email_verified,
                        profile=identity_profile_from_claims(claims),
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
            log_sso_event(
                "auth.sso.callback",
                result="mfa_required",
                reason="mfa_required",
                provider=normalized_provider,
                tenant_id=tenant_id,
                user_id=user_id,
            )
            raise
        except UserAuthenticationError as exc:
            log_sso_event(
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
            log_sso_event(
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
        try:
            tenant_configs = await self._provider_repository.list_for_tenant(
                tenant_id=tenant.id
            )
            global_configs = await self._provider_repository.list_for_tenant(tenant_id=None)
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
            record = await self._tenant_repository.get(resolved_id)
        elif tenant_slug:
            record = await self._tenant_repository.get_by_slug(tenant_slug)
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
            config = await self._provider_repository.fetch_with_fallback(
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
        identity = await self._identity_repository.get_by_subject(
            provider_key=provider_key,
            issuer=issuer,
            subject=subject,
        )
        user: UserRecord | None = None

        if identity is not None:
            user = await self._user_repository.get_user_by_id(identity.user_id)
            if user is None:
                raise SsoIdentityError(
                    "SSO identity references an unknown user.",
                    reason="identity_orphaned",
                )

        if user is None and email and email_verified:
            user = await self._user_repository.get_user_by_email(email)

        if user is not None:
            existing_identity = await self._identity_repository.get_by_user(
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


def _validate_nonce(claims: Mapping[str, Any], *, expected: str) -> None:
    nonce = claims.get("nonce")
    if not isinstance(nonce, str) or nonce != expected:
        raise SsoStateError(
            "SSO nonce validation failed.",
            reason="nonce_mismatch",
        )


__all__ = ["SsoService"]
