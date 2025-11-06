"""Authentication service helpers for service-account issuance."""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Sequence
from uuid import uuid4

from jose import jwt

from app.core.config import get_settings
from app.core.service_accounts import (
    ServiceAccountDefinition,
    ServiceAccountRegistry,
    ServiceAccountCatalogError,
    ServiceAccountNotFoundError,
    get_default_service_account_registry,
)


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

    def __init__(self, registry: ServiceAccountRegistry | None = None) -> None:
        if registry is None:
            try:
                registry = get_default_service_account_registry()
            except ServiceAccountCatalogError as exc:
                raise ServiceAccountCatalogUnavailable(str(exc)) from exc
        self._registry = registry
        self._lock = asyncio.Lock()
        self._per_account_window: dict[str, deque[datetime]] = {}
        self._global_window: deque[datetime] = deque()

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
                return existing

        issued_at = now
        expires_at = issued_at + timedelta(minutes=ttl_minutes)

        payload = {
            "sub": f"service-account:{account}",
            "account": account,
            "token_use": "refresh",
            "jti": str(uuid4()),
            "scope": " ".join(sanitized_scopes),
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        if tenant_id and definition.requires_tenant:
            payload["tenant_id"] = tenant_id

        if fingerprint:
            payload["fingerprint"] = fingerprint

        settings = get_settings()
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

        return {
            "refresh_token": token,
            "expires_at": expires_at.isoformat(),
            "issued_at": issued_at.isoformat(),
            "scopes": sanitized_scopes,
            "tenant_id": tenant_id if definition.requires_tenant else None,
            "kid": "legacy-hs256",  # Placeholder until EdDSA key management lands.
            "account": account,
            "token_use": "refresh",
        }

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
        """
        Placeholder for refresh-token reuse.

        Once the unified refresh-token store is implemented (AUTH-003),
        this method will query the store for an active token matching
        the account/tenant/scope tuple and return it when available.
        """

        # TODO: integrate with refresh-token repository once available.
        return None

    def _enforce_rate_limits(self, account: str, now: datetime) -> None:
        cutoff = now - timedelta(minutes=1)

        queue = self._per_account_window.setdefault(account, deque())
        while queue and queue[0] <= cutoff:
            queue.popleft()

        while self._global_window and self._global_window[0] <= cutoff:
            self._global_window.popleft()

        if len(queue) >= 5:
            raise ServiceAccountRateLimitError(
                f"Issuance rate limit exceeded for account '{account}'. Retry later."
            )

        if len(self._global_window) >= 30:
            raise ServiceAccountRateLimitError(
                "Global service-account issuance rate limit exceeded. Retry later."
            )

        queue.append(now)
        self._global_window.append(now)


auth_service = AuthService()
