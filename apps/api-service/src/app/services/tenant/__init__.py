"""Tenant platform services (settings, metadata)."""

from __future__ import annotations

from .tenant_account_service import (
    TenantAccountError,
    TenantAccountNotFoundError,
    TenantAccountService,
    TenantAccountSlugCollisionError,
    TenantAccountStatusError,
    TenantAccountValidationError,
    get_tenant_account_service,
    tenant_account_service,
)
from .tenant_lifecycle_service import (
    TenantLifecycleBillingError,
    TenantLifecycleError,
    TenantLifecycleService,
    build_tenant_lifecycle_service,
    get_tenant_lifecycle_service,
    tenant_lifecycle_service,
)
from .tenant_settings_service import (
    TenantSettingsError,
    TenantSettingsService,
    TenantSettingsValidationError,
    get_tenant_settings_service,
    tenant_settings_service,
)

__all__ = [
    "TenantAccountError",
    "TenantAccountNotFoundError",
    "TenantAccountService",
    "TenantAccountSlugCollisionError",
    "TenantAccountStatusError",
    "TenantAccountValidationError",
    "get_tenant_account_service",
    "tenant_account_service",
    "TenantLifecycleBillingError",
    "TenantLifecycleError",
    "TenantLifecycleService",
    "build_tenant_lifecycle_service",
    "get_tenant_lifecycle_service",
    "tenant_lifecycle_service",
    "TenantSettingsError",
    "TenantSettingsService",
    "TenantSettingsValidationError",
    "get_tenant_settings_service",
    "tenant_settings_service",
]
