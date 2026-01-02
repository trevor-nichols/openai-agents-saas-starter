"""User session orchestration helpers."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID, uuid4

from app.core.security import TokenVerifierError, get_token_verifier
from app.domain.auth import UserSessionListResult, UserSessionTokens
from app.domain.users import AuthenticatedUser
from app.observability.logging import log_event
from app.services.activity import activity_service
from app.services.auth.mfa_service import MfaService
from app.services.users import (
    InvalidCredentialsError,
    IpThrottledError,
    MembershipNotFoundError,
    TenantContextRequiredError,
    UserDisabledError,
    UserLockedError,
    UserService,
)

from .errors import MfaRequiredError, UserAuthenticationError, UserLogoutError, UserRefreshError
from .mfa_challenge_service import MfaChallenge, MfaChallengeService
from .refresh_token_manager import RefreshTokenManager
from .session_claims import parse_mfa_challenge_claims, parse_refresh_claims
from .session_store import SessionStore
from .session_token_issuer import issue_session_tokens


class TokenVerifierCallable(Protocol):
    def __call__(
        self,
        token: str,
        *,
        allow_expired: bool = False,
        error_cls: type[UserAuthenticationError] = UserRefreshError,
        error_message: str = "Refresh token verification failed.",
    ) -> dict[str, object]: ...


class UserSessionService:
    """Handles login, refresh, and lifecycle management for human sessions."""

    def __init__(
        self,
        *,
        refresh_tokens: RefreshTokenManager,
        session_store: SessionStore,
        user_service: UserService,
        token_verifier: TokenVerifierCallable | None = None,
        mfa_service: MfaService,
    ) -> None:
        self._refresh_tokens = refresh_tokens
        self._session_store = session_store
        self._user_service = user_service
        self._token_verifier: TokenVerifierCallable | None = token_verifier
        self._mfa_challenges = MfaChallengeService(mfa_service=mfa_service)

    def set_token_verifier(self, verifier: TokenVerifierCallable | None) -> None:
        self._token_verifier = verifier

    async def login_user(
        self,
        *,
        email: str,
        password: str,
        tenant_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> UserSessionTokens:
        service = self._user_service
        tenant_uuid = self._parse_uuid(tenant_id) if tenant_id else None
        try:
            auth_user = await service.authenticate(
                email=email,
                password=password,
                tenant_id=tenant_uuid,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except (
            InvalidCredentialsError,
            MembershipNotFoundError,
            UserLockedError,
            UserDisabledError,
            TenantContextRequiredError,
            IpThrottledError,
        ) as exc:
            raise UserAuthenticationError(str(exc)) from exc
        challenge = await self._maybe_return_mfa_challenge(
            auth_user,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        if challenge:
            raise MfaRequiredError(challenge.token, challenge.methods)
        return await self._issue_user_tokens(
            auth_user,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="login",
        )

    async def issue_tokens_for_user(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        ip_address: str | None,
        user_agent: str | None,
        reason: str,
        session_id: UUID | None = None,
        enforce_mfa: bool = True,
    ) -> UserSessionTokens:
        service = self._user_service
        try:
            auth_user = await service.load_active_user(
                user_id=user_id,
                tenant_id=tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except (
            InvalidCredentialsError,
            MembershipNotFoundError,
            UserLockedError,
            UserDisabledError,
            TenantContextRequiredError,
            IpThrottledError,
        ) as exc:
            raise UserAuthenticationError(str(exc)) from exc
        if enforce_mfa:
            challenge = await self._maybe_return_mfa_challenge(
                auth_user,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            if challenge:
                raise MfaRequiredError(challenge.token, challenge.methods)
        await service.record_login_success(
            user_id=auth_user.user_id,
            tenant_id=auth_user.tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason,
        )
        return await self._issue_user_tokens(
            auth_user,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason,
            session_id=session_id,
        )

    async def refresh_user_session(
        self,
        refresh_token: str,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> UserSessionTokens:
        payload = self._verify_token(refresh_token)
        claims = parse_refresh_claims(payload, error_cls=UserRefreshError, require_tenant=True)
        if claims.tenant_id is None:  # pragma: no cover - defensive
            raise UserRefreshError("Refresh token missing tenant identifier.")
        session_id = claims.session_id or uuid4()
        record = await self._refresh_tokens.get_by_jti(claims.jti)
        if not record:
            raise UserRefreshError("Refresh token has been revoked or expired.")
        await self._refresh_tokens.revoke(claims.jti, reason="rotated")
        service = self._user_service
        tenant_uuid = self._parse_uuid(claims.tenant_id)
        auth_user = await service.load_active_user(
            user_id=claims.user_id,
            tenant_id=tenant_uuid,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self._issue_user_tokens(
            auth_user,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="refresh",
            session_id=session_id,
        )

    async def logout_user_session(
        self,
        *,
        refresh_token: str,
        expected_user_id: str,
        reason: str = "user_logout",
    ) -> bool:
        payload = self._verify_token(
            refresh_token,
            allow_expired=True,
            error_cls=UserLogoutError,
            error_message="Refresh token verification failed.",
        )
        claims = parse_refresh_claims(payload, error_cls=UserLogoutError, require_tenant=False)
        token_user_id = claims.user_id
        try:
            caller_uuid = UUID(expected_user_id)
        except ValueError as exc:  # pragma: no cover - defensive
            raise UserLogoutError("Authenticated user identifier is invalid.") from exc
        if token_user_id != caller_uuid:
            raise UserLogoutError("Refresh token does not belong to the authenticated user.")

        record = await self._refresh_tokens.get_by_jti(claims.jti)
        if not record:
            return False
        if record.account != self._user_account_key(token_user_id):
            raise UserLogoutError("Refresh token ownership mismatch.")

        await self._refresh_tokens.revoke(claims.jti, reason=reason)
        await self._session_store.mark_session_revoked_by_jti(refresh_jti=claims.jti, reason=reason)
        log_event(
            "auth.session_revoke",
            result="success",
            user_id=str(token_user_id),
            revoked=1,
            reason=reason,
            tenant_id=record.tenant_id,
        )
        try:
            await activity_service.record(
                tenant_id=str(record.tenant_id),
                action="auth.logout",
                actor_id=str(token_user_id),
                actor_type="user",
                status="success",
                source="api",
                metadata={
                    "user_id": str(token_user_id),
                    "tenant_id": str(record.tenant_id),
                },
            )
        except Exception:  # pragma: no cover - best effort
            pass
        return True

    async def revoke_user_session_by_id(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        reason: str = "user_session_manual_revoke",
    ) -> bool:
        session = await self._session_store.get_session(session_id=session_id, user_id=user_id)
        if not session or session.revoked_at is not None:
            return False
        await self._refresh_tokens.revoke(session.refresh_jti, reason=reason)
        await self._session_store.mark_session_revoked(session_id=session_id, reason=reason)
        log_event(
            "auth.session_revoke",
            result="success",
            user_id=str(user_id),
            tenant_id=str(session.tenant_id),
            revoked=1,
            reason=reason,
            session_id=str(session_id),
        )
        return True

    async def list_user_sessions(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID | None,
        include_revoked: bool,
        limit: int,
        offset: int,
    ) -> UserSessionListResult:
        return await self._session_store.list_sessions(
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
        account = self._user_account_key(user_id)
        revoked = await self._refresh_tokens.revoke_account(account, reason=reason)
        await self._session_store.revoke_all_for_user(user_id=user_id, reason=reason)
        if revoked:
            log_event(
                "auth.session_revoke",
                result="success",
                user_id=str(user_id),
                revoked=revoked,
                reason=reason,
            )
        return revoked

    async def complete_mfa_challenge(
        self,
        *,
        challenge_token: str,
        method_id: UUID,
        code: str,
        ip_address: str | None,
        user_agent: str | None,
        ip_hash: str | None = None,
        user_agent_hash: str | None = None,
    ) -> UserSessionTokens:
        payload = self._verify_token(
            challenge_token,
            allow_expired=False,
            error_cls=UserAuthenticationError,
            error_message="MFA challenge token verification failed.",
        )
        claims = parse_mfa_challenge_claims(payload, error_cls=UserAuthenticationError)
        user_id = claims.user_id
        tenant_id = self._parse_uuid(claims.tenant_id)

        service = self._mfa_challenges.require_mfa_service()
        await service.verify_totp(
            user_id=user_id,
            method_id=method_id,
            code=code,
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
        )

        auth_user = await self._user_service.load_active_user(
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self._issue_user_tokens(
            auth_user,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="mfa",
            session_id=claims.session_id,
        )

    async def _issue_user_tokens(
        self,
        auth_user: AuthenticatedUser,
        *,
        ip_address: str | None,
        user_agent: str | None,
        reason: str,
        session_id: UUID | None = None,
    ) -> UserSessionTokens:
        issued = issue_session_tokens(
            auth_user,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
        )

        await self._session_store.upsert(
            session_id=issued.session_id,
            user_id=auth_user.user_id,
            tenant_id=auth_user.tenant_id,
            refresh_jti=issued.refresh_jti,
            fingerprint=issued.fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
            occurred_at=issued.issued_at,
        )
        await self._refresh_tokens.save(
            token=issued.refresh_token,
            account=issued.account,
            tenant_id=str(auth_user.tenant_id),
            scopes=auth_user.scopes,
            issued_at=issued.issued_at,
            expires_at=issued.refresh_expires_at,
            fingerprint=issued.fingerprint,
            signing_kid=issued.refresh_kid,
            session_id=issued.session_id,
            jti=issued.refresh_jti,
        )

        log_event(
            "auth.user_session",
            result="success",
            reason=reason,
            user_id=str(auth_user.user_id),
            tenant_id=str(auth_user.tenant_id),
        )

        return UserSessionTokens(
            access_token=issued.access_token,
            refresh_token=issued.refresh_token,
            expires_at=issued.access_expires_at,
            refresh_expires_at=issued.refresh_expires_at,
            kid=issued.access_kid,
            refresh_kid=issued.refresh_kid,
            scopes=auth_user.scopes,
            tenant_id=str(auth_user.tenant_id),
            user_id=str(auth_user.user_id),
            email_verified=auth_user.email_verified,
            session_id=str(issued.session_id),
        )

    def _verify_token(
        self,
        token: str,
        *,
        allow_expired: bool = False,
        error_cls: type[UserAuthenticationError] = UserRefreshError,
        error_message: str = "Refresh token verification failed.",
    ) -> dict[str, object]:
        if self._token_verifier is not None:
            return self._token_verifier(
                token,
                allow_expired=allow_expired,
                error_cls=error_cls,
                error_message=error_message,
            )
        return self._default_verify_token(
            token,
            allow_expired=allow_expired,
            error_cls=error_cls,
            error_message=error_message,
        )

    def _default_verify_token(
        self,
        token: str,
        *,
        allow_expired: bool = False,
        error_cls: type[UserAuthenticationError] = UserRefreshError,
        error_message: str = "Refresh token verification failed.",
    ) -> dict[str, object]:
        verifier = get_token_verifier()
        try:
            return verifier.verify(token, allow_expired=allow_expired)
        except TokenVerifierError as exc:
            raise error_cls(error_message) from exc

    async def _maybe_return_mfa_challenge(
        self,
        auth_user: AuthenticatedUser,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> MfaChallenge | None:
        return await self._mfa_challenges.maybe_issue_challenge(
            auth_user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def _user_account_key(self, user_id: UUID) -> str:
        return f"user:{user_id}"

    def _parse_uuid(self, value: str) -> UUID:
        try:
            return UUID(value)
        except ValueError as exc:  # pragma: no cover - defensive
            raise UserAuthenticationError("Invalid tenant identifier supplied.") from exc
