"""Feature flag request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.feature_flags import (
    TENANT_ENTITLEMENT_KEYS,
    FeatureEntitlementsSnapshot,
    FeatureKey,
    FeatureSnapshot,
)


class FeatureSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    billing_enabled: bool = Field(
        description="Whether billing APIs and UI flows are enabled for this tenant."
    )
    billing_stream_enabled: bool = Field(
        description="Whether billing event streaming is enabled for this tenant."
    )

    @classmethod
    def from_snapshot(cls, snapshot: FeatureSnapshot) -> FeatureSnapshotResponse:
        return cls(
            billing_enabled=snapshot.billing_enabled,
            billing_stream_enabled=snapshot.billing_stream_enabled,
        )


class TenantFeatureEntitlementsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    flags: dict[str, bool]

    @classmethod
    def from_snapshot(
        cls, snapshot: FeatureEntitlementsSnapshot
    ) -> TenantFeatureEntitlementsResponse:
        return cls(
            tenant_id=snapshot.tenant_id,
            flags={key.value: value for key, value in snapshot.entitlements.items()},
        )


class TenantFeatureEntitlementsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flags: dict[str, bool | None] = Field(
        description="Map of feature keys to enable/disable. Use null to clear override."
    )

    @field_validator("flags")
    @classmethod
    def _validate_flags(cls, value: dict[str, bool | None]) -> dict[str, bool | None]:
        allowed = {key.value for key in TENANT_ENTITLEMENT_KEYS}
        invalid = [key for key in value.keys() if key not in allowed]
        if invalid:
            raise ValueError(f"Unsupported feature flags: {', '.join(sorted(invalid))}.")
        return value

    def dict_for_service(self) -> dict[FeatureKey, bool | None]:
        return {FeatureKey(key): val for key, val in self.flags.items()}


__all__ = [
    "FeatureSnapshotResponse",
    "TenantFeatureEntitlementsResponse",
    "TenantFeatureEntitlementsUpdateRequest",
]
