"""Service-account token issuance helpers."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from time import perf_counter
from uuid import uuid4

from app.core.config import get_settings
from app.core.security import TokenSignerError, get_token_signer
from app.core.service_accounts import (
    ServiceAccountCatalogError,
    ServiceAccountDefinition,
    ServiceAccountNotFoundError,
    ServiceAccountRegistry,
    get_default_service_account_registry,
)
from app.domain.auth import ServiceAccountTokenListResult, ServiceAccountTokenStatus
from app.observability.logging import log_event
from app.observability.metrics import observe_service_account_issuance

from .errors import (
    ServiceAccountCatalogUnavailable,
    ServiceAccountError,
    ServiceAccountRateLimitError,
    ServiceAccountValidationError,
)
from .refresh_token_manager import RefreshTokenManager


class ServiceAccountTokenService:
    """Issues refresh tokens for machine-to-machine accounts with rate limiting."""

    def __init__(
        self,
        *,
        registry: ServiceAccountRegistry | None,
        refresh_tokens: RefreshTokenManager,
    ) -> None:
        if registry is None:
            try:
                registry = get_default_service_account_registry()
            except ServiceAccountCatalogError as exc:
                raise ServiceAccountCatalogUnavailable(str(exc)) from exc
        self._registry = registry
        self._refresh_tokens = refresh_tokens
        self._lock = asyncio.Lock()
        self._per_account_window: dict[str, deque[datetime]] = {}
        self._global_window: deque[datetime] = deque()

    async def issue_refresh_token(
        self,
        *,
        account: str,
        scopes: Sequence[str],
        tenant_id: str | None,
        requested_ttl_minutes: int | None,
        fingerprint: str | None,
        force: bool,
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
                existing = await self._refresh_tokens.find_active(
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
                    return self._refresh_tokens.record_to_response(existing)

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

            await self._refresh_tokens.save(
                token=signed.primary.token,
                account=account,
                tenant_id=tenant_id if definition.requires_tenant else None,
                scopes=list(sanitized_scopes),
                issued_at=issued_at,
                expires_at=expires_at,
                fingerprint=fingerprint,
                signing_kid=signed.primary.kid,
                session_id=None,
                jti=payload["jti"],
                require=False,
            )

            self._record_issuance_event(
                account=account,
                tenant_id=tenant_id,
                result="success",
                reason="success_issued",
                reused=False,
                started=started,
            )
            return {
                "refresh_token": signed.primary.token,
                "expires_at": expires_at.isoformat(),
                "issued_at": issued_at.isoformat(),
                "scopes": list(sanitized_scopes),
                "tenant_id": tenant_id if definition.requires_tenant else None,
                "kid": signed.primary.kid,
                "account": account,
                "token_use": "refresh",
                "session_id": None,
            }
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
        except Exception as exc:
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

    async def revoke_token(self, jti: str, *, reason: str | None) -> None:
        await self._refresh_tokens.revoke(jti, reason=reason, require=False)

    async def list_tokens(
        self,
        *,
        tenant_ids: Sequence[str] | None,
        include_global: bool,
        account_query: str | None,
        fingerprint: str | None,
        status: ServiceAccountTokenStatus,
        limit: int,
        offset: int,
    ) -> ServiceAccountTokenListResult:
        started = perf_counter()
        try:
            result = await self._refresh_tokens.list_tokens(
                tenant_ids=tenant_ids,
                include_global=include_global,
                account_query=account_query,
                fingerprint=fingerprint,
                status=status,
                limit=limit,
                offset=offset,
                require=False,
            )
            log_event(
                "service_account_tokens_list",
                result="success",
                tenant_scope="all" if tenant_ids is None else tenant_ids,
                include_global=include_global,
                account_query=bool(account_query),
                fingerprint=bool(fingerprint),
                status=status.value,
                duration_ms=(perf_counter() - started) * 1000,
            )
            return result
        except Exception as exc:  # pragma: no cover - logged & re-raised
            log_event(
                "service_account_tokens_list",
                result="error",
                reason=str(exc),
                tenant_scope="all" if tenant_ids is None else tenant_ids,
                include_global=include_global,
                status=status.value,
                duration_ms=(perf_counter() - started) * 1000,
            )
            raise

    def _validate_tenant(
        self, definition: ServiceAccountDefinition, tenant_id: str | None
    ) -> None:
        if definition.requires_tenant and not tenant_id:
            raise ServiceAccountValidationError(
                f"Service account '{definition.account}' requires a tenant identifier."
            )
        if not definition.requires_tenant and tenant_id:
            raise ServiceAccountValidationError(
                f"Service account '{definition.account}' does not accept tenant identifiers."
            )

    def _validate_scopes(
        self, definition: ServiceAccountDefinition, scopes: Sequence[str]
    ) -> list[str]:
        requested = {scope.strip() for scope in scopes if scope.strip()}
        if not requested:
            raise ServiceAccountValidationError("At least one scope must be requested.")
        if invalid := requested.difference(definition.allowed_scopes):
            raise ServiceAccountValidationError(
                "Unsupported scopes requested: " + ", ".join(sorted(invalid))
            )
        return sorted(requested)

    def _determine_ttl(
        self, definition: ServiceAccountDefinition, requested_ttl: int | None
    ) -> int:
        if requested_ttl is None:
            default_ttl = definition.default_ttl_minutes or definition.max_ttl_minutes
            return default_ttl
        if requested_ttl <= 0:
            raise ServiceAccountValidationError("Requested lifetime must be positive.")
        if requested_ttl > definition.max_ttl_minutes:
            raise ServiceAccountValidationError(
                f"Requested lifetime {requested_ttl} exceeds max {definition.max_ttl_minutes}"
                f" for account '{definition.account}'."
            )
        return requested_ttl

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
