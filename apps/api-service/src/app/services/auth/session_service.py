"""User session orchestration helpers."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

from app.core.security import TokenVerifierError, get_token_signer, get_token_verifier
from app.core.settings import get_settings
from app.domain.auth import UserSessionListResult, UserSessionTokens
from app.domain.users import AuthenticatedUser
from app.infrastructure.persistence.auth.models.mfa import UserMfaMethod
from app.observability.logging import log_event
from app.services.activity import activity_service
from app.services.auth.mfa_service import MfaService, get_mfa_service
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
from .refresh_token_manager import RefreshTokenManager
from .session_store import SessionStore


class TokenVerifierCallable(Protocol):
    def __call__(
        self,
        token: str,
        *,
        allow_expired: bool = False,
        error_cls: type[UserAuthenticationError] = UserRefreshError,
        error_message: str = "Refresh token verification failed.",
    ) -> dict[str, object]: ...


@dataclass
class MfaChallenge:
    token: str
    methods: list[dict[str, object]]


class UserSessionService:
    """Handles login, refresh, and lifecycle management for human sessions."""

    def __init__(
        self,
        *,
        refresh_tokens: RefreshTokenManager,
        session_store: SessionStore,
        user_service: UserService | None,
        token_verifier: TokenVerifierCallable | None = None,
        mfa_service: MfaService | None = None,
    ) -> None:
        self._refresh_tokens = refresh_tokens
        self._session_store = session_store
        self._user_service = user_service
        self._token_verifier: TokenVerifierCallable | None = token_verifier
        self._mfa_service = mfa_service

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
        service = self._require_user_service()
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
        service = self._require_user_service()
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
        if payload.get("token_use") != "refresh":
            raise UserRefreshError("Token is not a refresh token.")
        subject_claim = payload.get("sub")
        if not isinstance(subject_claim, str):
            raise UserRefreshError("Refresh token subject is malformed.")
        user_id = self._parse_user_subject(subject_claim)
        tenant_claim = payload.get("tenant_id")
        if not isinstance(tenant_claim, str) or not tenant_claim:
            raise UserRefreshError("Refresh token missing tenant identifier.")
        tenant_id = tenant_claim
        jti_claim = payload.get("jti")
        if not isinstance(jti_claim, str) or not jti_claim:
            raise UserRefreshError("Refresh token missing jti claim.")
        session_id = self._extract_session_id(payload) or uuid4()
        record = await self._refresh_tokens.get_by_jti(jti_claim)
        if not record:
            raise UserRefreshError("Refresh token has been revoked or expired.")
        await self._refresh_tokens.revoke(jti_claim, reason="rotated")
        service = self._require_user_service()
        tenant_uuid = self._parse_uuid(tenant_id)
        auth_user = await service.load_active_user(
            user_id=user_id,
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
        if payload.get("token_use") != "refresh":
            raise UserLogoutError("Token is not a refresh token.")

        subject_claim = payload.get("sub")
        if not isinstance(subject_claim, str):
            raise UserLogoutError("Refresh token subject is malformed.")
        try:
            token_user_id = self._parse_user_subject(subject_claim)
        except UserRefreshError as exc:
            raise UserLogoutError(str(exc)) from exc
        try:
            caller_uuid = UUID(expected_user_id)
        except ValueError as exc:  # pragma: no cover - defensive
            raise UserLogoutError("Authenticated user identifier is invalid.") from exc
        if token_user_id != caller_uuid:
            raise UserLogoutError("Refresh token does not belong to the authenticated user.")

        jti_claim = payload.get("jti")
        if not isinstance(jti_claim, str) or not jti_claim:
            raise UserLogoutError("Refresh token missing jti claim.")

        record = await self._refresh_tokens.get_by_jti(jti_claim)
        if not record:
            return False
        if record.account != self._user_account_key(token_user_id):
            raise UserLogoutError("Refresh token ownership mismatch.")

        await self._refresh_tokens.revoke(jti_claim, reason=reason)
        await self._session_store.mark_session_revoked_by_jti(refresh_jti=jti_claim, reason=reason)
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
        payload = self._default_verify_token(
            challenge_token,
            allow_expired=False,
            error_cls=UserAuthenticationError,
            error_message="MFA challenge token verification failed.",
        )
        if payload.get("token_use") != "mfa_challenge":
            raise UserAuthenticationError("Invalid MFA challenge token.")
        sub = payload.get("sub")
        tenant_claim = payload.get("tenant_id")
        session_id_claim = payload.get("sid")
        if not isinstance(sub, str) or not sub.startswith("user:"):
            raise UserAuthenticationError("Challenge token subject is malformed.")
        if not isinstance(tenant_claim, str):
            raise UserAuthenticationError("Challenge token missing tenant id.")
        if not isinstance(session_id_claim, str):
            raise UserAuthenticationError("Challenge token missing session id.")
        user_id = self._parse_user_subject(sub)
        tenant_id = self._parse_uuid(tenant_claim)
        try:
            session_id = UUID(session_id_claim)
        except ValueError as exc:  # pragma: no cover - defensive
            raise UserAuthenticationError("Challenge token session id is invalid.") from exc

        service = self._get_mfa_service()
        await service.verify_totp(
            user_id=user_id,
            method_id=method_id,
            code=code,
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
        )

        user_service = self._require_user_service()
        auth_user = await user_service.load_active_user(
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
            session_id=session_id,
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
        settings = get_settings()
        signer = get_token_signer(settings)
        issued_at = datetime.now(UTC)
        access_expires = issued_at + timedelta(minutes=settings.access_token_expire_minutes)
        audience = settings.auth_audience or [settings.app_name]
        session_uuid = session_id or uuid4()
        fingerprint = self._fingerprint(ip_address, user_agent)
        access_jti = str(uuid4())
        access_payload = {
            "sub": f"user:{auth_user.user_id}",
            "tenant_id": str(auth_user.tenant_id),
            "roles": [auth_user.role.value],
            "scope": " ".join(auth_user.scopes),
            "token_use": "access",
            "iss": settings.app_name,
            "aud": audience,
            "jti": access_jti,
            "email_verified": auth_user.email_verified,
            "sid": str(session_uuid),
            "iat": int(issued_at.timestamp()),
            "nbf": int(issued_at.timestamp()),
            "exp": int(access_expires.timestamp()),
        }
        signed_access = signer.sign(access_payload)

        refresh_ttl = getattr(settings, "auth_refresh_token_ttl_minutes", 43200)
        refresh_expires = issued_at + timedelta(minutes=refresh_ttl)
        account = self._user_account_key(auth_user.user_id)
        refresh_jti = str(uuid4())
        refresh_payload = {
            "sub": f"user:{auth_user.user_id}",
            "tenant_id": str(auth_user.tenant_id),
            "scope": " ".join(auth_user.scopes),
            "token_use": "refresh",
            "iss": settings.app_name,
            "email_verified": auth_user.email_verified,
            "jti": refresh_jti,
            "iat": int(issued_at.timestamp()),
            "nbf": int(issued_at.timestamp()),
            "exp": int(refresh_expires.timestamp()),
            "account": account,
            "sid": str(session_uuid),
        }
        signed_refresh = signer.sign(refresh_payload)

        await self._session_store.upsert(
            session_id=session_uuid,
            user_id=auth_user.user_id,
            tenant_id=auth_user.tenant_id,
            refresh_jti=refresh_jti,
            fingerprint=fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
            occurred_at=issued_at,
        )
        await self._refresh_tokens.save(
            token=signed_refresh.primary.token,
            account=account,
            tenant_id=str(auth_user.tenant_id),
            scopes=auth_user.scopes,
            issued_at=issued_at,
            expires_at=refresh_expires,
            fingerprint=fingerprint,
            signing_kid=signed_refresh.primary.kid,
            session_id=session_uuid,
            jti=refresh_jti,
        )

        log_event(
            "auth.user_session",
            result="success",
            reason=reason,
            user_id=str(auth_user.user_id),
            tenant_id=str(auth_user.tenant_id),
        )

        return UserSessionTokens(
            access_token=signed_access.primary.token,
            refresh_token=signed_refresh.primary.token,
            expires_at=access_expires,
            refresh_expires_at=refresh_expires,
            kid=signed_access.primary.kid,
            refresh_kid=signed_refresh.primary.kid,
            scopes=auth_user.scopes,
            tenant_id=str(auth_user.tenant_id),
            user_id=str(auth_user.user_id),
            email_verified=auth_user.email_verified,
            session_id=str(session_uuid),
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

    def _parse_user_subject(self, subject: str | None) -> UUID:
        if not subject or not subject.startswith("user:"):
            raise UserRefreshError("Refresh token subject is malformed.")
        try:
            return UUID(subject.split("user:", 1)[1])
        except ValueError as exc:  # pragma: no cover - defensive
            raise UserRefreshError("Refresh token subject is malformed.") from exc

    def _extract_session_id(self, payload: dict[str, object]) -> UUID | None:
        sid = payload.get("sid")
        if not isinstance(sid, str):
            return None
        try:
            return UUID(sid)
        except ValueError:  # pragma: no cover - defensive
            return None

    def _fingerprint(self, ip_address: str | None, user_agent: str | None) -> str | None:
        if not ip_address and not user_agent:
            return None
        material = f"{ip_address or ''}:{user_agent or ''}"
        encoded = base64.urlsafe_b64encode(material.encode("utf-8")).rstrip(b"=")
        return encoded.decode("utf-8")

    async def _maybe_return_mfa_challenge(
        self,
        auth_user: AuthenticatedUser,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> MfaChallenge | None:
        service = self._get_mfa_service()
        if service is None:
            return None
        needs_mfa, methods = await self._requires_mfa(service, auth_user.user_id)
        if not needs_mfa:
            return None
        return await self._issue_mfa_challenge(
            auth_user,
            methods,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def _requires_mfa(
        self, service: MfaService, user_id: UUID
    ) -> tuple[bool, list[UserMfaMethod]]:
        methods = await service.list_methods(user_id)
        verified = [m for m in methods if m.verified_at and not m.revoked_at]
        return bool(verified), verified

    async def _issue_mfa_challenge(
        self,
        auth_user: AuthenticatedUser,
        methods: list[UserMfaMethod],
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> MfaChallenge:
        settings = get_settings()
        signer = get_token_signer(settings)
        issued_at = datetime.now(UTC)
        expires = issued_at + timedelta(minutes=settings.mfa_challenge_ttl_minutes)
        session_uuid = uuid4()
        payload = {
            "sub": f"user:{auth_user.user_id}",
            "tenant_id": str(auth_user.tenant_id),
            "token_use": "mfa_challenge",
            "iss": settings.app_name,
            "aud": settings.auth_audience or [settings.app_name],
            "jti": str(uuid4()),
            "sid": str(session_uuid),
            "iat": int(issued_at.timestamp()),
            "nbf": int(issued_at.timestamp()),
            "exp": int(expires.timestamp()),
        }
        token = signer.sign(payload).primary.token
        method_payload = []
        for m in methods:
            method_payload.append(
                {
                    "id": m.id,
                    "method_type": getattr(m.method_type, "value", str(m.method_type)),
                    "label": m.label,
                    "verified_at": m.verified_at.isoformat() if m.verified_at else None,
                    "last_used_at": m.last_used_at.isoformat() if m.last_used_at else None,
                    "revoked_at": m.revoked_at.isoformat() if m.revoked_at else None,
                }
            )
        log_event(
            "auth.mfa_challenge",
            result="pending",
            user_id=str(auth_user.user_id),
            tenant_id=str(auth_user.tenant_id),
        )
        return MfaChallenge(token=token, methods=method_payload)

    def _get_mfa_service(self) -> MfaService:
        if self._mfa_service is not None:
            return self._mfa_service
        try:  # pragma: no cover - fallback
            self._mfa_service = get_mfa_service()
        except Exception as exc:  # pragma: no cover - defensive
            raise UserAuthenticationError("MFA service unavailable.") from exc
        return self._mfa_service

    def _user_account_key(self, user_id: UUID) -> str:
        return f"user:{user_id}"

    def _require_user_service(self) -> UserService:
        if self._user_service is None:
            from app.bootstrap.container import get_container

            container = get_container()
            if container.user_service is None:
                raise RuntimeError("UserService has not been configured.")
            self._user_service = container.user_service
        return self._user_service

    def _parse_uuid(self, value: str) -> UUID:
        try:
            return UUID(value)
        except ValueError as exc:  # pragma: no cover - defensive
            raise UserAuthenticationError("Invalid tenant identifier supplied.") from exc
