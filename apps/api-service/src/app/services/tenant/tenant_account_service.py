"""Service layer for tenant account lifecycle and metadata."""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from app.domain.tenant_accounts import (
    TenantAccount,
    TenantAccountCreate,
    TenantAccountListResult,
    TenantAccountRepository,
    TenantAccountSlugConflictError,
    TenantAccountStatus,
    TenantAccountStatusUpdate,
    TenantAccountUpdate,
)

SlugGenerator = Callable[[str], str]
Clock = Callable[[], datetime]

_MAX_SLUG_LENGTH = 64
_MAX_NAME_LENGTH = 128
_MIN_NAME_LENGTH = 2
_SLUG_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")

_ALLOWED_TRANSITIONS: dict[TenantAccountStatus, set[TenantAccountStatus]] = {
    TenantAccountStatus.PROVISIONING: {
        TenantAccountStatus.ACTIVE,
        TenantAccountStatus.DEPROVISIONING,
    },
    TenantAccountStatus.ACTIVE: {
        TenantAccountStatus.SUSPENDED,
        TenantAccountStatus.DEPROVISIONING,
    },
    TenantAccountStatus.SUSPENDED: {
        TenantAccountStatus.ACTIVE,
        TenantAccountStatus.DEPROVISIONING,
    },
    TenantAccountStatus.DEPROVISIONING: {TenantAccountStatus.DEPROVISIONED},
    TenantAccountStatus.DEPROVISIONED: set(),
}


class TenantAccountError(Exception):
    """Base error for tenant account operations."""


class TenantAccountNotFoundError(TenantAccountError):
    """Raised when a tenant account cannot be located."""


class TenantAccountValidationError(TenantAccountError):
    """Raised when tenant account input fails validation."""


class TenantAccountSlugCollisionError(TenantAccountError):
    """Raised when a tenant slug is already taken."""


class TenantAccountStatusError(TenantAccountError):
    """Raised when an invalid lifecycle transition is attempted."""


class TenantAccountService:
    """Encapsulates tenant account validation and lifecycle transitions."""

    def __init__(
        self,
        repository: TenantAccountRepository | None = None,
        *,
        slug_generator: SlugGenerator | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._repository = repository
        self._slug_generator = slug_generator or self._default_slugify
        self._clock = clock or (lambda: datetime.now(UTC))

    def set_repository(self, repository: TenantAccountRepository) -> None:
        self._repository = repository

    def with_repository(self, repository: TenantAccountRepository) -> TenantAccountService:
        return TenantAccountService(
            repository=repository,
            slug_generator=self._slug_generator,
            clock=self._clock,
        )

    @property
    def repository(self) -> TenantAccountRepository:
        return self._require_repository()

    def _require_repository(self) -> TenantAccountRepository:
        if self._repository is None:
            raise RuntimeError("Tenant account repository has not been configured.")
        return self._repository

    async def get_account(self, tenant_id: UUID) -> TenantAccount:
        account = await self._require_repository().get(tenant_id)
        if account is None:
            raise TenantAccountNotFoundError("Tenant account not found.")
        return account

    async def complete_provisioning(
        self,
        tenant_id: UUID,
        *,
        actor_user_id: UUID | None,
        reason: str | None,
    ) -> TenantAccount:
        account = await self.get_account(tenant_id)
        if account.status == TenantAccountStatus.ACTIVE:
            return account
        self._ensure_transition(account.status, TenantAccountStatus.ACTIVE)
        occurred_at = self._clock()
        return await self._update_status(
            tenant_id,
            TenantAccountStatus.ACTIVE,
            actor_user_id=actor_user_id,
            reason=reason,
            occurred_at=occurred_at,
        )

    async def list_accounts(
        self,
        *,
        limit: int,
        offset: int,
        status: TenantAccountStatus | None = None,
        query: str | None = None,
    ) -> TenantAccountListResult:
        return await self._require_repository().list(
            limit=limit,
            offset=offset,
            status=status,
            query=query,
        )

    async def create_account(
        self,
        *,
        name: str,
        slug: str | None = None,
        status: TenantAccountStatus = TenantAccountStatus.ACTIVE,
        created_by_user_id: UUID | None = None,
        reason: str | None = None,
        allow_slug_suffix: bool = True,
    ) -> TenantAccount:
        normalized_name = self._normalize_name(name)
        if slug is None:
            base_slug = self._slug_generator(normalized_name)
            normalized_slug = self._normalize_slug(base_slug)
            resolved_slug = await self._ensure_unique_slug(
                normalized_slug, allow_suffix=allow_slug_suffix
            )
        else:
            normalized_slug = self._normalize_slug(slug)
            resolved_slug = await self._ensure_unique_slug(
                normalized_slug, allow_suffix=allow_slug_suffix
            )

        payload = TenantAccountCreate(
            name=normalized_name,
            slug=resolved_slug,
            status=status,
            status_updated_by=created_by_user_id,
            status_reason=reason,
        )
        try:
            return await self._require_repository().create(payload)
        except TenantAccountSlugConflictError as exc:
            raise TenantAccountSlugCollisionError(str(exc)) from exc

    async def update_account(
        self,
        tenant_id: UUID,
        *,
        name: str | None = None,
        slug: str | None = None,
        allow_slug_change: bool = False,
    ) -> TenantAccount:
        update = TenantAccountUpdate(
            name=self._normalize_name(name) if name is not None else None,
            slug=None,
        )

        if slug is not None:
            if not allow_slug_change:
                raise TenantAccountValidationError("Tenant slug is immutable for this operation.")
            normalized_slug = self._normalize_slug(slug)
            await self._ensure_slug_available(normalized_slug, tenant_id=tenant_id)
            update.slug = normalized_slug

        try:
            record = await self._require_repository().update(tenant_id, update)
        except TenantAccountSlugConflictError as exc:
            raise TenantAccountSlugCollisionError(str(exc)) from exc
        if record is None:
            raise TenantAccountNotFoundError("Tenant account not found.")
        return record

    async def suspend_account(
        self,
        tenant_id: UUID,
        *,
        actor_user_id: UUID | None,
        reason: str | None,
    ) -> TenantAccount:
        account = await self.get_account(tenant_id)
        if account.status == TenantAccountStatus.SUSPENDED:
            return account
        self._ensure_transition(account.status, TenantAccountStatus.SUSPENDED)
        occurred_at = self._clock()
        return await self._update_status(
            tenant_id,
            TenantAccountStatus.SUSPENDED,
            actor_user_id=actor_user_id,
            reason=reason,
            occurred_at=occurred_at,
            suspended_at=occurred_at,
        )

    async def reactivate_account(
        self,
        tenant_id: UUID,
        *,
        actor_user_id: UUID | None,
        reason: str | None,
    ) -> TenantAccount:
        account = await self.get_account(tenant_id)
        if account.status == TenantAccountStatus.ACTIVE:
            return account
        self._ensure_transition(account.status, TenantAccountStatus.ACTIVE)
        occurred_at = self._clock()
        return await self._update_status(
            tenant_id,
            TenantAccountStatus.ACTIVE,
            actor_user_id=actor_user_id,
            reason=reason,
            occurred_at=occurred_at,
        )

    async def deprovision_account(
        self,
        tenant_id: UUID,
        *,
        actor_user_id: UUID | None,
        reason: str | None,
    ) -> TenantAccount:
        account = await self.get_account(tenant_id)
        if account.status == TenantAccountStatus.DEPROVISIONED:
            return account
        if account.status != TenantAccountStatus.DEPROVISIONING:
            await self.begin_deprovision(
                tenant_id,
                actor_user_id=actor_user_id,
                reason=reason,
            )
        return await self.finalize_deprovision(
            tenant_id,
            actor_user_id=actor_user_id,
            reason=reason,
        )

    def ensure_active(self, account: TenantAccount) -> None:
        if account.status != TenantAccountStatus.ACTIVE:
            raise TenantAccountStatusError(
                "Tenant account is not active for this operation."
            )

    async def begin_deprovision(
        self,
        tenant_id: UUID,
        *,
        actor_user_id: UUID | None,
        reason: str | None,
    ) -> TenantAccount:
        account = await self.get_account(tenant_id)
        if account.status == TenantAccountStatus.DEPROVISIONING:
            return account
        if account.status == TenantAccountStatus.DEPROVISIONED:
            return account
        self._ensure_transition(account.status, TenantAccountStatus.DEPROVISIONING)
        occurred_at = self._clock()
        return await self._update_status(
            tenant_id,
            TenantAccountStatus.DEPROVISIONING,
            actor_user_id=actor_user_id,
            reason=reason,
            occurred_at=occurred_at,
        )

    async def finalize_deprovision(
        self,
        tenant_id: UUID,
        *,
        actor_user_id: UUID | None,
        reason: str | None,
    ) -> TenantAccount:
        account = await self.get_account(tenant_id)
        if account.status == TenantAccountStatus.DEPROVISIONED:
            return account
        if account.status != TenantAccountStatus.DEPROVISIONING:
            raise TenantAccountStatusError(
                "Tenant account must be deprovisioning before finalization."
            )
        occurred_at = self._clock()
        return await self._update_status(
            tenant_id,
            TenantAccountStatus.DEPROVISIONED,
            actor_user_id=actor_user_id,
            reason=reason,
            occurred_at=occurred_at,
            deprovisioned_at=occurred_at,
        )

    async def _update_status(
        self,
        tenant_id: UUID,
        status: TenantAccountStatus,
        *,
        actor_user_id: UUID | None,
        reason: str | None,
        occurred_at: datetime,
        suspended_at: datetime | None = None,
        deprovisioned_at: datetime | None = None,
    ) -> TenantAccount:
        update = TenantAccountStatusUpdate(
            status=status,
            occurred_at=occurred_at,
            updated_by=actor_user_id,
            reason=reason,
            suspended_at=suspended_at,
            deprovisioned_at=deprovisioned_at,
        )
        record = await self._require_repository().update_status(tenant_id, update)
        if record is None:
            raise TenantAccountNotFoundError("Tenant account not found.")
        return record

    async def _ensure_unique_slug(self, slug: str, *, allow_suffix: bool) -> str:
        if not allow_suffix:
            await self._ensure_slug_available(slug)
            return slug

        candidate = slug
        attempts = 0
        while await self._slug_exists(candidate):
            attempts += 1
            suffix = secrets.token_hex(2)
            max_base = max(1, _MAX_SLUG_LENGTH - len(suffix) - 1)
            trimmed = slug[:max_base]
            candidate = f"{trimmed}-{suffix}"
            if attempts > 10:
                raise TenantAccountSlugCollisionError(
                    "Unable to allocate a unique tenant slug."
                )
        return candidate

    async def _slug_exists(self, slug: str) -> bool:
        record = await self._require_repository().get_by_slug(slug)
        return record is not None

    async def _ensure_slug_available(
        self, slug: str, *, tenant_id: UUID | None = None
    ) -> None:
        record = await self._require_repository().get_by_slug(slug)
        if record is None:
            return
        if tenant_id is not None and record.id == tenant_id:
            return
        raise TenantAccountSlugCollisionError("Tenant slug already exists.")

    def _ensure_transition(
        self,
        current: TenantAccountStatus,
        target: TenantAccountStatus,
    ) -> None:
        if target == current:
            return
        if target not in _ALLOWED_TRANSITIONS.get(current, set()):
            raise TenantAccountStatusError(
                f"Cannot transition tenant from {current.value} to {target.value}."
            )

    def _normalize_name(self, value: str | None) -> str:
        if value is None:
            raise TenantAccountValidationError("Tenant name is required.")
        normalized = value.strip()
        if len(normalized) < _MIN_NAME_LENGTH:
            raise TenantAccountValidationError(
                "Tenant name must be at least 2 characters."
            )
        if len(normalized) > _MAX_NAME_LENGTH:
            raise TenantAccountValidationError(
                f"Tenant name must be <= {_MAX_NAME_LENGTH} characters."
            )
        return normalized

    def _normalize_slug(self, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise TenantAccountValidationError("Tenant slug is required.")
        if len(normalized) > _MAX_SLUG_LENGTH:
            raise TenantAccountValidationError(
                f"Tenant slug must be <= {_MAX_SLUG_LENGTH} characters."
            )
        if not _SLUG_PATTERN.match(normalized):
            raise TenantAccountValidationError(
                "Tenant slug must be lowercase alphanumeric with optional hyphens."
            )
        return normalized

    @staticmethod
    def _default_slugify(value: str) -> str:
        normalized = value.strip().lower()
        normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
        return normalized[:_MAX_SLUG_LENGTH] or "tenant"


def get_tenant_account_service() -> TenantAccountService:
    from app.bootstrap.container import get_container

    return get_container().tenant_account_service


class _TenantAccountHandle:
    def __getattr__(self, name: str):
        if name == "get_tenant_account_service":
            return get_tenant_account_service
        return getattr(get_tenant_account_service(), name)


tenant_account_service = _TenantAccountHandle()


__all__ = [
    "TenantAccountError",
    "TenantAccountNotFoundError",
    "TenantAccountService",
    "TenantAccountSlugCollisionError",
    "TenantAccountStatusError",
    "TenantAccountValidationError",
    "tenant_account_service",
    "get_tenant_account_service",
]
