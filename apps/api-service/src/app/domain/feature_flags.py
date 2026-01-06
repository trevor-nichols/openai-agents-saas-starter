"""Domain models for feature flag evaluation and entitlements."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum


class FeatureKey(str, Enum):
    """Canonical feature keys supported by the platform."""

    BILLING = "billing"
    BILLING_STREAM = "billing_stream"


FEATURE_FLAG_PREFIX = "feature."
TENANT_ENTITLEMENT_KEYS: set[FeatureKey] = {FeatureKey.BILLING}


def tenant_feature_key(key: FeatureKey) -> str:
    return f"{FEATURE_FLAG_PREFIX}{key.value}"


def is_reserved_feature_flag(key: str) -> bool:
    return key.startswith(FEATURE_FLAG_PREFIX)


def split_feature_flags(
    flags: Mapping[str, bool] | None,
) -> tuple[dict[str, bool], dict[str, bool]]:
    reserved: dict[str, bool] = {}
    custom: dict[str, bool] = {}
    if not flags:
        return reserved, custom
    for key, value in flags.items():
        if is_reserved_feature_flag(key):
            reserved[key] = bool(value)
        else:
            custom[key] = bool(value)
    return reserved, custom


def extract_tenant_entitlements(flags: Mapping[str, bool] | None) -> dict[FeatureKey, bool]:
    if not flags:
        return {}
    entitlements: dict[FeatureKey, bool] = {}
    for feature_key in TENANT_ENTITLEMENT_KEYS:
        raw_key = tenant_feature_key(feature_key)
        if raw_key in flags:
            entitlements[feature_key] = bool(flags[raw_key])
    return entitlements


@dataclass(slots=True)
class FeatureSnapshot:
    """Effective feature state for a tenant."""

    billing_enabled: bool
    billing_stream_enabled: bool

    def is_enabled(self, key: FeatureKey) -> bool:
        if key is FeatureKey.BILLING:
            return self.billing_enabled
        if key is FeatureKey.BILLING_STREAM:
            return self.billing_stream_enabled
        return False


@dataclass(slots=True)
class FeatureEntitlementsSnapshot:
    """Tenant-level feature entitlements managed by platform operators."""

    tenant_id: str
    entitlements: dict[FeatureKey, bool]


__all__ = [
    "FEATURE_FLAG_PREFIX",
    "FeatureEntitlementsSnapshot",
    "FeatureKey",
    "FeatureSnapshot",
    "TENANT_ENTITLEMENT_KEYS",
    "extract_tenant_entitlements",
    "is_reserved_feature_flag",
    "split_feature_flags",
    "tenant_feature_key",
]
