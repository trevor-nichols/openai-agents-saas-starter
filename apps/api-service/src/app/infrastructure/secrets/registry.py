"""Provider registry used to build the configured SecretProvider."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping

from app.core.settings import Settings, get_settings
from app.domain.secrets import SecretProviderProtocol, SecretsProviderLiteral

from .aws_provider import build_aws_secret_provider
from .azure_provider import build_azure_secret_provider
from .infisical_provider import build_infisical_secret_provider
from .vault_provider import build_vault_secret_provider

ProviderFactory = Callable[[Settings], SecretProviderProtocol]
logger = logging.getLogger(__name__)


def _build_registry() -> Mapping[SecretsProviderLiteral, ProviderFactory]:
    return {
        SecretsProviderLiteral.VAULT_DEV: build_vault_secret_provider,
        SecretsProviderLiteral.VAULT_HCP: build_vault_secret_provider,
        SecretsProviderLiteral.INFISICAL_CLOUD: build_infisical_secret_provider,
        SecretsProviderLiteral.INFISICAL_SELF_HOST: build_infisical_secret_provider,
        SecretsProviderLiteral.AWS_SM: build_aws_secret_provider,
        SecretsProviderLiteral.AZURE_KV: build_azure_secret_provider,
    }


_PROVIDER_CACHE: SecretProviderProtocol | None = None
_PROVIDER_KEY: SecretsProviderLiteral | None = None


def reset_secret_provider_cache() -> None:
    """Clear cached provider (test helper)."""

    global _PROVIDER_CACHE, _PROVIDER_KEY
    _PROVIDER_CACHE = None
    _PROVIDER_KEY = None


def get_secret_provider(settings: Settings | None = None) -> SecretProviderProtocol:
    """Return (and cache) the configured SecretProvider implementation."""

    global _PROVIDER_CACHE, _PROVIDER_KEY
    settings = settings or get_settings()
    provider_key = settings.secrets_provider

    if _PROVIDER_CACHE and provider_key == _PROVIDER_KEY:
        return _PROVIDER_CACHE

    registry = _build_registry()
    try:
        factory = registry[provider_key]
    except KeyError as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Secrets provider {provider_key!r} is not registered.") from exc

    provider = factory(settings)
    _PROVIDER_CACHE = provider
    _PROVIDER_KEY = provider_key
    if settings.enable_secrets_provider_telemetry:
        logger.info("Initialized secrets provider", extra={"secrets_provider": provider_key.value})
    return provider


__all__ = ["get_secret_provider", "reset_secret_provider_cache"]
