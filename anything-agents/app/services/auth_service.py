"""Authentication service helpers for service and human accounts."""

from __future__ import annotations

import asyncio
import base64
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from time import perf_counter
from uuid import UUID, uuid4

import jwt

from app.core.config import get_settings
from app.core.security import (
    TokenSignerError,
    TokenVerifierError,
    get_token_signer,
    get_token_verifier,
)
from app.core.service_accounts import (
    ServiceAccountCatalogError,
    ServiceAccountDefinition,
    ServiceAccountNotFoundError,
    ServiceAccountRegistry,
    get_default_service_account_registry,
)
from app.domain.auth import RefreshTokenRecord, RefreshTokenRepository
from app.domain.users import AuthenticatedUser
from app.infrastructure.persistence.auth.repository import (
    get_refresh_token_repository,
)
from app.observability.logging import log_event
from app.observability.metrics import observe_service_account_issuance
from app.services.user_service import (
    InvalidCredentialsError,
    IpThrottledError,
    MembershipNotFoundError,
    TenantContextRequiredError,
    UserDisabledError,
    UserLockedError,
    UserService,
    get_user_service,
)


class ServiceAccountError(RuntimeError):
    """Base class for service-account issuance errors."""


class ServiceAccountValidationError(ServiceAccountError):
    """Raised when the request fails validation checks."""


class ServiceAccountRateLimitError(ServiceAccountError):
    """Raised when issuance requests exceed configured limits."""


class ServiceAccountCatalogUnavailable(ServiceAccountError):
    """Raised when the service-account catalog cannot be loaded."""


class UserAuthenticationError(RuntimeError):
    """Base class for human authentication failures."""


class UserRefreshError(UserAuthenticationError):
    """Raised when refresh tokens fail validation."""


@dataclass(slots=True)
class UserSessionTokens:
    access_token: str
    refresh_token: str
    expires_at: datetime
    refresh_expires_at: datetime
    kid: str
    refresh_kid: str
    scopes: list[str]
    tenant_id: str
    user_id: str
    token_type: str = "bearer"


class AuthService:
    """Core authentication helper providing service-account token issuance."""

    def __init__(
        self,
        registry: ServiceAccountRegistry | None = None,
        refresh_repository: RefreshTokenRepository | None = None,
        user_service: UserService | None = None,
    ) -> None:
        if registry is None:
            try:
                registry = get_default_service_account_registry()
            except ServiceAccountCatalogError as exc:
                raise ServiceAccountCatalogUnavailable(str(exc)) from exc
        self._registry = registry
        self._lock = asyncio.Lock()
        self._per_account_window: dict[str, deque[datetime]] = {}
        self._global_window: deque[datetime] = deque()
        self._refresh_repo = refresh_repository or get_refresh_token_repository()
        self._user_service = user_service

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
        started = perf_counter()
        failure_recorded = False
        try:
            try:
                definition = self._registry.get(account)
            except ServiceAccountNotFoundError as exc:
                raise ServiceAccountValidationError(str(exc)) from exc

            now = datetime.now(UTC)
            async with self._lock:
                self._enforce_rate_limits(account, now)

            self._validate_tenant(definition, tenant_id)
            sanitized_scopes = self._validate_scopes(definition, scopes)
            ttl_minutes = self._determine_ttl(definition, requested_ttl_minutes)

            if not force:
                existing = await self._find_active_token(
                    account=account,
                    tenant_id=tenant_id,
                    scopes=sanitized_scopes,
                )
                if existing is not None:
                    self._record_issuance_event(
                        account=account,
                        tenant_id=tenant_id,
                        result="success",
                        reason="success_reused",
                        reused=True,
                        started=started,
                        detail="returned_cached_token",
                    )
                    return existing

            issued_at = now
            expires_at = issued_at + timedelta(minutes=ttl_minutes)
            settings = get_settings()

            payload = {
                "sub": f"service-account:{account}",
                "account": account,
                "token_use": "refresh",
                "jti": str(uuid4()),
                "scope": " ".join(sanitized_scopes),
                "iat": int(issued_at.timestamp()),
                "nbf": int(issued_at.timestamp()),
                "exp": int(expires_at.timestamp()),
                "iss": settings.app_name,
            }

            if tenant_id and definition.requires_tenant:
                payload["tenant_id"] = tenant_id

            if fingerprint:
                payload["fingerprint"] = fingerprint

            signer = get_token_signer(settings)
            try:
                signed = signer.sign(payload)
            except TokenSignerError as exc:
                failure_recorded = True
                self._record_issuance_event(
                    account=account,
                    tenant_id=tenant_id,
                    result="failure",
                    reason="signer_error",
                    reused=False,
                    started=started,
                    detail=str(exc),
                    level="error",
                )
                raise ServiceAccountError(f"Failed to sign refresh token: {exc}") from exc
            token = signed.primary.token
            signing_kid = signed.primary.kid

            response = {
                "refresh_token": token,
                "expires_at": expires_at.isoformat(),
                "issued_at": issued_at.isoformat(),
                "scopes": sanitized_scopes,
                "tenant_id": tenant_id if definition.requires_tenant else None,
                "kid": signing_kid,
                "account": account,
                "token_use": "refresh",
            }
            await self._persist_refresh_token(
                token=token,
                account=account,
                tenant_id=tenant_id if definition.requires_tenant else None,
                scopes=sanitized_scopes,
                issued_at=issued_at,
                expires_at=expires_at,
                fingerprint=fingerprint,
                signing_kid=signing_kid,
            )
            self._record_issuance_event(
                account=account,
                tenant_id=tenant_id if definition.requires_tenant else None,
                result="success",
                reason="success_new",
                reused=False,
                started=started,
            )
            return response
        except ServiceAccountValidationError as exc:
            if not failure_recorded:
                self._record_issuance_event(
                    account=account,
                    tenant_id=tenant_id,
                    result="failure",
                    reason="validation_error",
                    reused=False,
                    started=started,
                    detail=str(exc),
                    level="warning",
                )
            raise
        except ServiceAccountRateLimitError as exc:
            if not failure_recorded:
                self._record_issuance_event(
                    account=account,
                    tenant_id=tenant_id,
                    result="failure",
                    reason="rate_limited",
                    reused=False,
                    started=started,
                    detail=str(exc),
                    level="warning",
                )
            raise
        except ServiceAccountCatalogUnavailable as exc:
            if not failure_recorded:
                self._record_issuance_event(
                    account=account,
                    tenant_id=tenant_id,
                    result="failure",
                    reason="catalog_unavailable",
                    reused=False,
                    started=started,
                    detail=str(exc),
                    level="error",
                )
            raise
        except ServiceAccountError as exc:
            if not failure_recorded:
                self._record_issuance_event(
                    account=account,
                    tenant_id=tenant_id,
                    result="failure",
                    reason="service_error",
                    reused=False,
                    started=started,
                    detail=str(exc),
                    level="error",
                )
            raise

    async def login_user(
        self,
        *,
        email: str,
        password: str,
        tenant_id: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
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
        return await self._issue_user_tokens(
            auth_user,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="login",
        )

    async def refresh_user_session(
        self,
        refresh_token: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserSessionTokens:
        repo = self._ensure_refresh_repository()
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
        record = await repo.get_by_jti(jti_claim)
        if not record:
            raise UserRefreshError("Refresh token has been revoked or expired.")
        await repo.revoke(jti_claim, reason="rotated")
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
        )

    def _validate_tenant(self, definition: ServiceAccountDefinition, tenant_id: str | None) -> None:
        if definition.requires_tenant and not tenant_id:
            raise ServiceAccountValidationError(
                f"Service account '{definition.account}' requires a tenant identifier."
            )
        if not definition.requires_tenant:
            # Normalize global accounts to omit tenant_id downstream.
            if tenant_id:
                raise ServiceAccountValidationError(
                    f"Service account '{definition.account}' is global; omit tenant_id."
                )

    def _validate_scopes(
        self, definition: ServiceAccountDefinition, scopes: Sequence[str]
    ) -> list[str]:
        if not scopes:
            raise ServiceAccountValidationError("At least one scope must be provided.")

        sanitized = [scope.strip() for scope in scopes if scope.strip()]
        if not sanitized:
            raise ServiceAccountValidationError("Scopes cannot be empty strings.")

        invalid = [scope for scope in sanitized if scope not in definition.allowed_scopes]
        if invalid:
            raise ServiceAccountValidationError(
                f"Scopes {invalid} are not permitted for account '{definition.account}'."
            )

        # Preserve ordering but deduplicate identical scopes.
        deduped: list[str] = []
        for scope in sanitized:
            if scope not in deduped:
                deduped.append(scope)
        return deduped

    def _determine_ttl(
        self, definition: ServiceAccountDefinition, requested_ttl_minutes: int | None
    ) -> int:
        if requested_ttl_minutes is None:
            return definition.default_ttl_minutes or definition.max_ttl_minutes

        if requested_ttl_minutes <= 0:
            raise ServiceAccountValidationError("lifetime_minutes must be greater than zero.")

        if requested_ttl_minutes > definition.max_ttl_minutes:
            raise ServiceAccountValidationError(
                f"Requested lifetime {requested_ttl_minutes} exceeds max "
                f"{definition.max_ttl_minutes} for account '{definition.account}'."
            )
        return requested_ttl_minutes

    async def _find_active_token(
        self,
        *,
        account: str,
        tenant_id: str | None,
        scopes: list[str],
    ) -> dict[str, str | int | list[str] | None] | None:
        if not self._refresh_repo:
            return None
        record = await self._refresh_repo.find_active(account, tenant_id, scopes)
        if not record:
            return None
        return self._record_to_response(record)

    async def _issue_user_tokens(
        self,
        auth_user: AuthenticatedUser,
        *,
        ip_address: str | None,
        user_agent: str | None,
        reason: str,
    ) -> UserSessionTokens:
        settings = get_settings()
        self._ensure_refresh_repository()
        signer = get_token_signer(settings)
        issued_at = datetime.now(UTC)
        access_expires = issued_at + timedelta(minutes=settings.access_token_expire_minutes)
        audience = settings.auth_audience or [settings.app_name]
        access_payload = {
            "sub": f"user:{auth_user.user_id}",
            "tenant_id": str(auth_user.tenant_id),
            "roles": [auth_user.role],
            "scope": " ".join(auth_user.scopes),
            "token_use": "access",
            "iss": settings.app_name,
            "aud": audience,
            "jti": str(uuid4()),
            "iat": int(issued_at.timestamp()),
            "nbf": int(issued_at.timestamp()),
            "exp": int(access_expires.timestamp()),
        }
        signed_access = signer.sign(access_payload)

        refresh_ttl = getattr(settings, "auth_refresh_token_ttl_minutes", 43200)
        refresh_expires = issued_at + timedelta(minutes=refresh_ttl)
        refresh_payload = {
            "sub": f"user:{auth_user.user_id}",
            "tenant_id": str(auth_user.tenant_id),
            "scope": " ".join(auth_user.scopes),
            "token_use": "refresh",
            "iss": settings.app_name,
            "jti": str(uuid4()),
            "iat": int(issued_at.timestamp()),
            "nbf": int(issued_at.timestamp()),
            "exp": int(refresh_expires.timestamp()),
            "account": self._user_account_key(auth_user.user_id),
        }
        signed_refresh = signer.sign(refresh_payload)

        await self._persist_refresh_token(
            token=signed_refresh.primary.token,
            account=self._user_account_key(auth_user.user_id),
            tenant_id=str(auth_user.tenant_id),
            scopes=auth_user.scopes,
            issued_at=issued_at,
            expires_at=refresh_expires,
            fingerprint=self._fingerprint(ip_address, user_agent),
            signing_kid=signed_refresh.primary.kid,
            jti=refresh_payload["jti"],
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
        )

    def _verify_token(self, token: str) -> dict[str, object]:
        verifier = get_token_verifier()
        try:
            return verifier.verify(token)
        except TokenVerifierError as exc:
            raise UserRefreshError("Refresh token verification failed.") from exc

    def _parse_user_subject(self, subject: str | None) -> UUID:
        if not subject or not subject.startswith("user:"):
            raise UserRefreshError("Refresh token subject is malformed.")
        try:
            return UUID(subject.split("user:", 1)[1])
        except ValueError as exc:  # pragma: no cover - defensive
            raise UserRefreshError("Refresh token subject is malformed.") from exc

    def _fingerprint(self, ip_address: str | None, user_agent: str | None) -> str | None:
        if not ip_address and not user_agent:
            return None
        material = f"{ip_address or ''}:{user_agent or ''}"
        encoded = base64.urlsafe_b64encode(material.encode("utf-8")).rstrip(b"=")
        return encoded.decode("utf-8")

    def _user_account_key(self, user_id: UUID) -> str:
        return f"user:{user_id}"

    def _ensure_refresh_repository(self) -> RefreshTokenRepository:
        repo = self._refresh_repo or get_refresh_token_repository()
        if repo is None:
            raise RuntimeError("Refresh-token repository is not configured.")
        self._refresh_repo = repo
        return repo

    def _require_user_service(self) -> UserService:
        if self._user_service is None:
            self._user_service = get_user_service()
        return self._user_service

    def _parse_uuid(self, value: str) -> UUID:
        try:
            return UUID(value)
        except ValueError as exc:  # pragma: no cover - defensive
            raise UserAuthenticationError("Invalid tenant identifier supplied.") from exc

    def _enforce_rate_limits(self, account: str, now: datetime) -> None:
        cutoff = now - timedelta(minutes=1)

        queue = self._per_account_window.setdefault(account, deque())
        while queue and queue[0] <= cutoff:
            queue.popleft()

        while self._global_window and self._global_window[0] <= cutoff:
            self._global_window.popleft()

        if len(queue) >= 5:
            log_event(
                "service_account_rate_limit",
                level="warning",
                account=account,
                limit_type="per_account",
                in_flight=len(queue),
            )
            raise ServiceAccountRateLimitError(
                f"Issuance rate limit exceeded for account '{account}'. Retry later."
            )

        if len(self._global_window) >= 30:
            log_event(
                "service_account_rate_limit",
                level="warning",
                account=account,
                limit_type="global",
                in_flight=len(self._global_window),
            )
            raise ServiceAccountRateLimitError(
                "Global service-account issuance rate limit exceeded. Retry later."
            )

        queue.append(now)
        self._global_window.append(now)

    async def _persist_refresh_token(
        self,
        *,
        token: str,
        account: str,
        tenant_id: str | None,
        scopes: list[str],
        issued_at: datetime,
        expires_at: datetime,
        fingerprint: str | None,
        signing_kid: str,
        jti: str | None = None,
    ) -> None:
        if not self._refresh_repo:
            return
        record = RefreshTokenRecord(
            token=token,
            jti=jti or self._extract_jti(token),
            account=account,
            tenant_id=tenant_id,
            scopes=scopes,
            expires_at=expires_at,
            issued_at=issued_at,
            fingerprint=fingerprint,
            signing_kid=signing_kid,
        )
        await self._refresh_repo.save(record)

    async def revoke_service_account_token(self, jti: str, *, reason: str | None = None) -> None:
        if not self._refresh_repo:
            return
        await self._refresh_repo.revoke(jti, reason=reason)

    async def revoke_user_sessions(
        self,
        user_id: UUID,
        *,
        reason: str = "password_change",
    ) -> int:
        repo = self._ensure_refresh_repository()
        account = self._user_account_key(user_id)
        revoked = await repo.revoke_account(account, reason=reason)
        if revoked:
            log_event(
                "auth.session_revoke",
                result="success",
                user_id=str(user_id),
                revoked=revoked,
                reason=reason,
            )
        return revoked

    def _record_to_response(
        self, record: RefreshTokenRecord
    ) -> dict[str, str | int | list[str] | None]:
        kid = record.signing_kid or self._extract_kid(record.token)
        return {
            "refresh_token": record.token,
            "expires_at": record.expires_at.isoformat(),
            "issued_at": record.issued_at.isoformat(),
            "scopes": record.scopes,
            "tenant_id": record.tenant_id,
            "kid": kid,
            "account": record.account,
            "token_use": "refresh",
        }

    def _extract_jti(self, token: str) -> str:
        try:
            payload = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
        except Exception:
            return str(uuid4())
        value = payload.get("jti")
        return str(value) if value else str(uuid4())

    def _extract_kid(self, token: str) -> str:
        try:
            header = jwt.get_unverified_header(token)
        except Exception:
            return "unknown"
        kid = header.get("kid")
        return str(kid) if kid else "unknown"

    def _record_issuance_event(
        self,
        *,
        account: str,
        tenant_id: str | None,
        result: str,
        reason: str,
        reused: bool,
        started: float,
        detail: str | None = None,
        level: str = "info",
    ) -> None:
        duration = perf_counter() - started
        observe_service_account_issuance(
            account=account,
            result=result,
            reason=reason,
            reused=reused,
            duration_seconds=duration,
        )
        log_event(
            "service_account_issuance",
            level=level,
            account=account,
            tenant_id=tenant_id,
            result=result,
            reason=reason,
            reused=reused,
            duration_seconds=duration,
            detail=detail,
        )


auth_service = AuthService()
