"""Tenant persistence adapters."""

from .account_repository import PostgresTenantAccountRepository
from .postgres import PostgresTenantSettingsRepository

__all__ = ["PostgresTenantAccountRepository", "PostgresTenantSettingsRepository"]
