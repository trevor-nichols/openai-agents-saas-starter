"""Tenant context helpers for multi-tenant aware endpoints."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status

from app.api.dependencies.auth import CurrentUser, require_verified_user
from app.api.dependencies.platform import OperatorOverride, resolve_operator_override
from app.domain.tenant_accounts import TenantAccountStatus
from app.domain.tenant_roles import (
    ROLE_PRIORITY,
    TenantRole,
    max_tenant_role,
    normalize_tenant_role,
)
from app.observability.logging import bind_log_context, log_event
from app.services.tenant.tenant_account_service import (
    TenantAccountNotFoundError,
    TenantAccountService,
    get_tenant_account_service,
)
from app.services.users.scopes import role_for_scopes


class TenantContext:
    """Lightweight representation of the active tenant request scope."""

    def __init__(
        self,
        tenant_id: str,
        role: TenantRole,
        user: dict[str, Any],
    ) -> None:
        self.tenant_id = tenant_id
        self.role = role
        self.user = user

    def ensure_role(self, *allowed: TenantRole) -> None:
        if self.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient tenant privileges for this operation.",
            )


async def get_tenant_context(
    request: Request,
    tenant_id_header: str | None = Header(None, alias="X-Tenant-Id"),
    tenant_role_header: str | None = Header(None, alias="X-Tenant-Role"),
    operator_override_header: str | None = Header(None, alias="X-Operator-Override"),
    operator_reason_header: str | None = Header(None, alias="X-Operator-Reason"),
    current_user: CurrentUser = Depends(require_verified_user()),
    tenant_account_service: TenantAccountService = Depends(get_tenant_account_service),
) -> TenantContext:
    """Resolve tenant context using JWT claims (headers may only down-scope access)."""

    header_tenant = tenant_id_header if isinstance(tenant_id_header, str) else None
    header_role = tenant_role_header if isinstance(tenant_role_header, str) else None
    operator_override = (
        operator_override_header if isinstance(operator_override_header, str) else None
    )
    operator_reason = (
        operator_reason_header if isinstance(operator_reason_header, str) else None
    )

    payload_obj = current_user.get("payload")
    payload: dict[str, Any]
    if isinstance(payload_obj, dict):
        payload = payload_obj
    else:
        payload = {}
    token_tenant = payload.get("tenant_id")
    effective_tenant = token_tenant

    if effective_tenant:
        if header_tenant and header_tenant != effective_tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant mismatch between token and X-Tenant-Id header.",
            )
    else:
        if not header_tenant:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated token is missing tenant context.",
            )
        effective_tenant = header_tenant

    if not effective_tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated token is missing tenant context.",
        )

    granted_role = _role_from_claims(payload)
    requested_role = _normalize_role(header_role)
    role = _select_effective_role(granted_role, requested_role)

    bind_log_context(
        tenant_id=effective_tenant,
        tenant_role=role.value,
        user_id=current_user.get("user_id"),
    )

    override_context = resolve_operator_override(
        operator_override=operator_override,
        operator_reason=operator_reason,
        current_user=current_user,
    )
    await _enforce_tenant_status(
        effective_tenant,
        request=request,
        override=override_context,
        tenant_account_service=tenant_account_service,
    )

    return TenantContext(tenant_id=effective_tenant, role=role, user=current_user)


def require_tenant_role(*allowed: TenantRole):
    """Dependency factory enforcing that the caller has one of the allowed roles."""

    async def _dependency(
        context: TenantContext = Depends(get_tenant_context),
    ) -> TenantContext:
        context.ensure_role(*allowed)
        return context

    return _dependency


def _role_from_claims(payload: dict[str, Any]) -> TenantRole:
    roles_claim = payload.get("roles")
    role = _role_from_roles(roles_claim)
    if role is not None:
        return role

    scope_claim = payload.get("scope")
    role = _role_from_scopes(scope_claim)
    return role or TenantRole.VIEWER


def _role_from_roles(roles_claim: Any) -> TenantRole | None:
    if roles_claim is None:
        return None
    if isinstance(roles_claim, str):
        return normalize_tenant_role(roles_claim)
    if isinstance(roles_claim, Sequence):
        resolved: TenantRole | None = None
        for value in roles_claim:
            resolved = max_tenant_role(resolved, normalize_tenant_role(value))
        return resolved
    return None


def _role_from_scopes(scope_claim: Any) -> TenantRole | None:
    scopes: Iterable[str] = []
    if isinstance(scope_claim, str):
        scopes = scope_claim.split()
    elif isinstance(scope_claim, Sequence):
        scopes = [str(item) for item in scope_claim]
    return role_for_scopes(scopes)


def _select_effective_role(
    granted: TenantRole | None,
    requested: TenantRole | None,
) -> TenantRole:
    effective = granted or TenantRole.VIEWER
    if requested is None:
        return effective

    if ROLE_PRIORITY[requested] > ROLE_PRIORITY[effective]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requested tenant role exceeds privileges granted by token.",
        )
    return requested


def _normalize_role(value: Any) -> TenantRole | None:
    return normalize_tenant_role(value)


_READ_ONLY_METHODS = {"GET", "HEAD", "OPTIONS"}


async def _enforce_tenant_status(
    tenant_id: str,
    *,
    request: Request,
    override: OperatorOverride | None,
    tenant_account_service: TenantAccountService,
) -> None:
    tenant_uuid = _parse_tenant_uuid(tenant_id)
    try:
        account = await tenant_account_service.get_account(tenant_uuid)
    except TenantAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if account.status == TenantAccountStatus.ACTIVE:
        return

    if account.status == TenantAccountStatus.SUSPENDED:
        if override is not None and _is_readonly_request(request):
            _log_operator_override(tenant_id, request, override)
            return
        if override is not None and not _is_readonly_request(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator override is read-only for suspended tenants.",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is suspended.",
        )

    if account.status == TenantAccountStatus.DEPROVISIONING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is deprovisioning.",
        )

    if account.status == TenantAccountStatus.DEPROVISIONED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is deprovisioned.",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Tenant account is not active.",
    )


def _parse_tenant_uuid(tenant_id: str) -> UUID:
    try:
        return UUID(str(tenant_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context must be a valid UUID.",
        ) from exc


def _is_readonly_request(request: Request) -> bool:
    return request.method.upper() in _READ_ONLY_METHODS


def _log_operator_override(
    tenant_id: str,
    request: Request,
    override: OperatorOverride,
) -> None:
    try:
        log_event(
            "tenant.access.override",
            tenant_id=tenant_id,
            actor_id=override.actor_id,
            reason=override.reason,
            method=request.method if request else None,
            path=str(request.url.path) if request else None,
        )
    except Exception:  # pragma: no cover - best effort logging
        pass
