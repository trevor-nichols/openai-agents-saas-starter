"""Authentication service facade wiring cohesive sub-services."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from app.core.service_accounts import ServiceAccountRegistry
from app.domain.auth import (
    RefreshTokenRepository,
    UserSessionListResult,
    UserSessionRepository,
    UserSessionTokens,
)
from app.infrastructure.persistence.auth.repository import get_refresh_token_repository
from app.infrastructure.persistence.auth.session_repository import get_user_session_repository
from app.services.auth import (
    RefreshTokenManager,
    ServiceAccountTokenService,
    SessionStore,
    UserSessionService,
)
from app.services.auth.errors import (
    ServiceAccountCatalogUnavailable,
    ServiceAccountError,
    ServiceAccountRateLimitError,
    ServiceAccountValidationError,
    UserAuthenticationError,
    UserLogoutError,
    UserRefreshError,
)
from app.services.geoip_service import GeoIPService, get_geoip_service
from app.services.user_service import UserService


class AuthService:
    """Thin façade delegating to specialized auth sub-services."""

    def __init__(
        self,
        registry: ServiceAccountRegistry | None = None,
        *,
        refresh_repository: RefreshTokenRepository | None = None,
        user_service: UserService | None = None,
        session_repository: UserSessionRepository | None = None,
        geoip_service: GeoIPService | None = None,
    ) -> None:
        refresh_repo = refresh_repository or get_refresh_token_repository()
        session_repo = session_repository or get_user_session_repository()
        geoip = geoip_service or get_geoip_service()
        refresh_tokens = RefreshTokenManager(refresh_repo)
        session_store = SessionStore(session_repo, geoip)
        self._service_accounts = ServiceAccountTokenService(
            registry=registry,
            refresh_tokens=refresh_tokens,
        )
        self._sessions = UserSessionService(
            refresh_tokens=refresh_tokens,
            session_store=session_store,
            user_service=user_service,
        )

        def _forward_verify_token(
            token: str,
            *,
            allow_expired: bool = False,
            error_cls: type[UserAuthenticationError] = UserRefreshError,
            error_message: str = "Refresh token verification failed.",
        ) -> dict[str, object]:
            return self._verify_token(
                token,
                allow_expired=allow_expired,
                error_cls=error_cls,
                error_message=error_message,
            )

        self._sessions.set_token_verifier(_forward_verify_token)

    async def issue_service_account_refresh_token(
        self,
        *,
        account: str,
        scopes: Sequence[str],
        tenant_id: str | None,
        requested_ttl_minutes: int | None,
        fingerprint: str | None,
        force: bool = False,
    ) -> dict[str, str | int | list[str] | None]:
        return await self._service_accounts.issue_refresh_token(
            account=account,
            scopes=scopes,
            tenant_id=tenant_id,
            requested_ttl_minutes=requested_ttl_minutes,
            fingerprint=fingerprint,
            force=force,
        )

    async def revoke_service_account_token(
        self, jti: str, *, reason: str | None = None
    ) -> None:
        await self._service_accounts.revoke_token(jti, reason=reason)

    async def login_user(
        self,
        *,
        email: str,
        password: str,
        tenant_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserSessionTokens:
        return await self._sessions.login_user(
            email=email,
            password=password,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def refresh_user_session(
        self,
        refresh_token: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserSessionTokens:
        return await self._sessions.refresh_user_session(
            refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def logout_user_session(
        self,
        *,
        refresh_token: str,
        expected_user_id: str,
        reason: str = "user_logout",
    ) -> bool:
        return await self._sessions.logout_user_session(
            refresh_token=refresh_token,
            expected_user_id=expected_user_id,
            reason=reason,
        )

    async def revoke_user_session_by_id(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        reason: str = "user_session_manual_revoke",
    ) -> bool:
        return await self._sessions.revoke_user_session_by_id(
            user_id=user_id,
            session_id=session_id,
            reason=reason,
        )

    async def list_user_sessions(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID | None = None,
        include_revoked: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> UserSessionListResult:
        return await self._sessions.list_user_sessions(
            user_id=user_id,
            tenant_id=tenant_id,
            include_revoked=include_revoked,
            limit=limit,
            offset=offset,
        )

    async def revoke_user_sessions(
        self,
        user_id: UUID,
        *,
        reason: str = "password_change",
    ) -> int:
        return await self._sessions.revoke_user_sessions(user_id, reason=reason)

    # Backwards-compatible hooks used in unit tests.
    def _verify_token(
        self,
        token: str,
        *,
        allow_expired: bool = False,
        error_cls: type[UserAuthenticationError] = UserRefreshError,
        error_message: str = "Refresh token verification failed.",
    ) -> dict[str, object]:
        return self._sessions._default_verify_token(  # type: ignore[attr-defined]
            token,
            allow_expired=allow_expired,
            error_cls=error_cls,
            error_message=error_message,
        )


auth_service = AuthService()

__all__ = [
    "AuthService",
    "auth_service",
    "ServiceAccountError",
    "ServiceAccountValidationError",
    "ServiceAccountRateLimitError",
    "ServiceAccountCatalogUnavailable",
    "UserAuthenticationError",
    "UserRefreshError",
    "UserLogoutError",
    "UserSessionTokens",
]
