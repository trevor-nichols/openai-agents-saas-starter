"""Compatibility shim re-exporting provider validation helpers."""

from starter_contracts.provider_validation import (
    ProviderSettingsProtocol,
    ProviderViolation,
    ensure_provider_parity,
    validate_providers,
)

__all__ = [
    "ProviderSettingsProtocol",
    "ProviderViolation",
    "ensure_provider_parity",
    "validate_providers",
]
