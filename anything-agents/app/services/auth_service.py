"""Authentication service helpers for service-account issuance."""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Sequence
from uuid import uuid4

import jwt

from app.core.config import get_settings
from app.core.security import get_token_signer, TokenSignerError
from app.domain.auth import RefreshTokenRecord, RefreshTokenRepository
from app.core.service_accounts import (
    ServiceAccountDefinition,
    ServiceAccountRegistry,
    ServiceAccountCatalogError,
    ServiceAccountNotFoundError,
    get_default_service_account_registry,
)
from app.infrastructure.persistence.auth.repository import (
    get_refresh_token_repository,
)
from app.observability.logging import log_event
from app.observability.metrics import observe_service_account_issuance


class ServiceAccountError(RuntimeError):
    """Base class for service-account issuance errors."""


class ServiceAccountValidationError(ServiceAccountError):
    """Raised when the request fails validation checks."""


class ServiceAccountRateLimitError(ServiceAccountError):
    """Raised when issuance requests exceed configured limits."""


class ServiceAccountCatalogUnavailable(ServiceAccountError):
    """Raised when the service-account catalog cannot be loaded."""


class AuthService:
    """Core authentication helper providing service-account token issuance."""

    def __init__(
        self,
        registry: ServiceAccountRegistry | None = None,
        refresh_repository: RefreshTokenRepository | None = None,
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

    async def issue_service_account_refresh_token(
        self,
        *,
        account: str,
        scopes: Sequence[str],
        tenant_id: str | None,
        requested_ttl_minutes: int | None,
        fingerprint: str | None,
        force: bool = False,
    ) -> dict[str, str | int | None]:
        started = perf_counter()
        failure_recorded = False
        try:
            try:
                definition = self._registry.get(account)
            except ServiceAccountNotFoundError as exc:
                raise ServiceAccountValidationError(str(exc)) from exc

            now = datetime.now(timezone.utc)
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

    def _validate_tenant(
        self, definition: ServiceAccountDefinition, tenant_id: str | None
    ) -> None:
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
    ) -> dict[str, str | int | None] | None:
        if not self._refresh_repo:
            return None
        record = await self._refresh_repo.find_active(account, tenant_id, scopes)
        if not record:
            return None
        return self._record_to_response(record)

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
    ) -> None:
        if not self._refresh_repo:
            return
        record = RefreshTokenRecord(
            token=token,
            jti=self._extract_jti(token),
            account=account,
            tenant_id=tenant_id,
            scopes=scopes,
            expires_at=expires_at,
            issued_at=issued_at,
            fingerprint=fingerprint,
            signing_kid=signing_kid,
        )
        await self._refresh_repo.save(record)

    async def revoke_service_account_token(
        self, jti: str, *, reason: str | None = None
    ) -> None:
        if not self._refresh_repo:
            return
        await self._refresh_repo.revoke(jti, reason=reason)

    def _record_to_response(
        self, record: RefreshTokenRecord
    ) -> dict[str, str | int | None]:
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
        except Exception:  # noqa: BLE001
            return str(uuid4())
        value = payload.get("jti")
        return str(value) if value else str(uuid4())

    def _extract_kid(self, token: str) -> str:
        try:
            header = jwt.get_unverified_header(token)
        except Exception:  # noqa: BLE001
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
