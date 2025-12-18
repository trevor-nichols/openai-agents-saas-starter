"""Shared dependencies for workflow API endpoints."""

from __future__ import annotations

from app.api.dependencies.tenant import TenantRole, require_tenant_role

WORKFLOW_ALLOWED_ROLES: tuple[TenantRole, ...] = (
    TenantRole.VIEWER,
    TenantRole.ADMIN,
    TenantRole.OWNER,
)

WORKFLOW_ADMIN_ROLES: tuple[TenantRole, ...] = (
    TenantRole.ADMIN,
    TenantRole.OWNER,
)

require_workflow_viewer_role = require_tenant_role(*WORKFLOW_ALLOWED_ROLES)
require_workflow_admin_role = require_tenant_role(*WORKFLOW_ADMIN_ROLES)

__all__ = [
    "WORKFLOW_ALLOWED_ROLES",
    "WORKFLOW_ADMIN_ROLES",
    "require_workflow_viewer_role",
    "require_workflow_admin_role",
]

