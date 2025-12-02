"""Modular settings package exporting the aggregated Settings object."""
from __future__ import annotations

from functools import lru_cache

from .activity import ActivitySettingsMixin
from .ai import AIProviderSettingsMixin
from .application import ApplicationSettingsMixin
from .base import VAULT_PROVIDER_KEYS, BaseAppSettings, SignupAccessPolicyLiteral
from .database import DatabaseAndBillingSettingsMixin
from .integrations import IntegrationSettingsMixin
from .mcp import MCPSettingsMixin
from .observability import ObservabilitySettingsMixin
from .providers import SecretsProviderSettingsMixin
from .rate_limits import RateLimitSettingsMixin
from .redis import RedisSettingsMixin
from .retention import RetentionSettingsMixin
from .security import SecuritySettingsMixin
from .signup import SignupSettingsMixin
from .storage import StorageSettingsMixin
from .usage import UsageGuardrailSettingsMixin


class Settings(
    BaseAppSettings,
    AIProviderSettingsMixin,
    ApplicationSettingsMixin,
    ActivitySettingsMixin,
    MCPSettingsMixin,
    IntegrationSettingsMixin,
    RedisSettingsMixin,
    RateLimitSettingsMixin,
    SignupSettingsMixin,
    SecuritySettingsMixin,
    SecretsProviderSettingsMixin,
    DatabaseAndBillingSettingsMixin,
    ObservabilitySettingsMixin,
    RetentionSettingsMixin,
    UsageGuardrailSettingsMixin,
    StorageSettingsMixin,
):
    """Concrete application settings composed from mixins."""


@lru_cache
def get_settings() -> Settings:
    return Settings()


def enforce_secret_overrides(settings: Settings, *, force: bool = False) -> None:
    issues = settings.secret_warnings()
    if not issues:
        return
    if force or settings.should_enforce_secret_overrides():
        formatted = "; ".join(issues)
        raise RuntimeError(
            "Production environment cannot start with default secrets. "
            f"Fix the following: {formatted}"
        )


def enforce_vault_verification(settings: Settings) -> None:
    if not settings.should_require_vault_verification():
        return
    if settings.secrets_provider not in VAULT_PROVIDER_KEYS:
        return
    if not settings.vault_verify_enabled:
        raise RuntimeError(
            "Vault verification is required outside local/dev environments. "
            "Set VAULT_VERIFY_ENABLED=true via the Starter CLI or env files."
        )
    missing = settings.vault_requirements_missing()
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            "Vault verification is enabled but incomplete. "
            f"Configure {joined} or rerun the Starter CLI wizard."
        )


__all__ = [
    "Settings",
    "SignupAccessPolicyLiteral",
    "get_settings",
    "enforce_secret_overrides",
    "enforce_vault_verification",
]
