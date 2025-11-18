"""Entitlement loader that syncs usage guardrail plans into Postgres."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine


class EntitlementLoaderError(Exception):
    """Raised when entitlement syncing fails."""


class _FeatureModel(BaseModel):
    feature_key: str = Field(..., alias="feature_key")
    display_name: str
    unit: str | None = None
    is_metered: bool = True
    soft_limit: int | None = None
    hard_limit: int | None = None


class _PlanModel(BaseModel):
    plan_code: str
    features: list[_FeatureModel] = Field(default_factory=list)


class _ArtifactModel(BaseModel):
    generated_at: datetime | None = None
    enabled: bool = False
    plans: list[_PlanModel] = Field(default_factory=list)


@dataclass(slots=True)
class PlanSyncResult:
    plan_code: str
    inserted: int = 0
    updated: int = 0
    pruned: int = 0


@dataclass(slots=True)
class UsageEntitlementSyncResult:
    artifact_path: Path
    artifact_generated_at: datetime | None
    artifact_enabled: bool
    dry_run: bool
    plan_results: list[PlanSyncResult]

    @property
    def total_inserted(self) -> int:
        return sum(result.inserted for result in self.plan_results)

    @property
    def total_updated(self) -> int:
        return sum(result.updated for result in self.plan_results)

    @property
    def total_pruned(self) -> int:
        return sum(result.pruned for result in self.plan_results)

    @property
    def plans_processed(self) -> int:
        return len(self.plan_results)


_PLAN_LOOKUP = text(
    """
    SELECT id
    FROM billing_plans
    WHERE code = :code
    LIMIT 1
    """
)

_EXISTING_FEATURES = text(
    """
    SELECT id, feature_key, display_name, hard_limit, soft_limit, is_metered
    FROM plan_features
    WHERE plan_id = :plan_id
    """
)

_INSERT_FEATURE = text(
    """
    INSERT INTO plan_features (
        plan_id,
        feature_key,
        display_name,
        description,
        hard_limit,
        soft_limit,
        is_metered
    ) VALUES (
        :plan_id,
        :feature_key,
        :display_name,
        :description,
        :hard_limit,
        :soft_limit,
        :is_metered
    )
    """
)

_UPDATE_FEATURE = text(
    """
    UPDATE plan_features
    SET
        display_name = :display_name,
        hard_limit = :hard_limit,
        soft_limit = :soft_limit,
        is_metered = :is_metered
    WHERE id = :feature_id
    """
)

_DELETE_FEATURE = text(
    """
    DELETE FROM plan_features
    WHERE id = :feature_id
    """
)


async def sync_usage_entitlements(
    *,
    database_url: str,
    artifact_path: Path,
    plan_filter: Iterable[str] | None = None,
    prune_missing: bool = False,
    dry_run: bool = False,
    allow_disabled_artifact: bool = False,
) -> UsageEntitlementSyncResult:
    """Sync plan features from the CLI artifact into the billing database."""

    artifact = _load_artifact(artifact_path)
    if not artifact.enabled and not allow_disabled_artifact:
        raise EntitlementLoaderError(
            "The usage entitlements artifact is disabled. Rerun the setup wizard with "
            "guardrails enabled or pass --allow-disabled-artifact to override."
        )

    plan_codes = _normalize_plan_filter(plan_filter)
    plans = _filter_plans(artifact.plans, plan_codes)
    if not plans:
        raise EntitlementLoaderError("No plans matched the provided filters.")

    engine = create_async_engine(database_url)
    results: list[PlanSyncResult] = []
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                for plan in plans:
                    result = await _sync_plan(
                        connection,
                        plan,
                        prune_missing=prune_missing,
                        dry_run=dry_run,
                    )
                    results.append(result)
                if dry_run:
                    await transaction.rollback()
                else:
                    await transaction.commit()
            except Exception:
                await transaction.rollback()
                raise
    finally:
        await engine.dispose()

    return UsageEntitlementSyncResult(
        artifact_path=artifact_path,
        artifact_generated_at=artifact.generated_at,
        artifact_enabled=artifact.enabled,
        dry_run=dry_run,
        plan_results=results,
    )


def _normalize_plan_filter(plan_filter: Iterable[str] | None) -> set[str] | None:
    if plan_filter is None:
        return None
    cleaned = {code.strip().lower() for code in plan_filter if code and code.strip()}
    return cleaned or None


def _filter_plans(
    plans: Sequence[_PlanModel],
    plan_filter: set[str] | None,
) -> list[_PlanModel]:
    if plan_filter is None:
        return list(plans)
    return [plan for plan in plans if plan.plan_code.lower() in plan_filter]


async def _sync_plan(
    connection: AsyncConnection,
    plan: _PlanModel,
    *,
    prune_missing: bool,
    dry_run: bool,
) -> PlanSyncResult:
    plan_id = await _fetch_plan_id(connection, plan.plan_code)
    existing = await _fetch_existing_features(connection, plan_id)
    result = PlanSyncResult(plan_code=plan.plan_code)

    desired: dict[str, dict[str, object]] = {}
    for feature in plan.features:
        desired[feature.feature_key] = {
            "display_name": feature.display_name,
            "hard_limit": feature.hard_limit,
            "soft_limit": feature.soft_limit,
            "is_metered": feature.is_metered,
        }

    for feature in plan.features:
        payload = desired[feature.feature_key]
        if feature.feature_key not in existing:
            result.inserted += 1
            if not dry_run:
                await connection.execute(
                    _INSERT_FEATURE,
                    {
                        "plan_id": plan_id,
                        "feature_key": feature.feature_key,
                        "display_name": payload["display_name"],
                        "description": None,
                        "hard_limit": payload["hard_limit"],
                        "soft_limit": payload["soft_limit"],
                        "is_metered": payload["is_metered"],
                    },
                )
        else:
            row = existing[feature.feature_key]
            if _needs_update(row, payload):
                result.updated += 1
                if not dry_run:
                    await connection.execute(
                        _UPDATE_FEATURE,
                        {
                            "feature_id": row["id"],
                            "display_name": payload["display_name"],
                            "hard_limit": payload["hard_limit"],
                            "soft_limit": payload["soft_limit"],
                            "is_metered": payload["is_metered"],
                        },
                    )

    if prune_missing and existing:
        desired_keys = set(desired.keys())
        for feature_key, row in existing.items():
            if feature_key in desired_keys:
                continue
            result.pruned += 1
            if not dry_run:
                await connection.execute(
                    _DELETE_FEATURE,
                    {"feature_id": row["id"]},
                )

    return result


async def _fetch_plan_id(connection: AsyncConnection, plan_code: str) -> str:
    try:
        result = await connection.execute(_PLAN_LOOKUP, {"code": plan_code})
    except SQLAlchemyError as exc:  # pragma: no cover - defensive
        raise EntitlementLoaderError(str(exc)) from exc
    plan_id = result.scalar_one_or_none()
    if plan_id is None:
        raise EntitlementLoaderError(
            f"Plan '{plan_code}' does not exist. Seed plans via Stripe or migrations first."
        )
    return str(plan_id)


async def _fetch_existing_features(
    connection: AsyncConnection, plan_id: str
) -> dict[str, dict[str, object]]:
    try:
        result = await connection.execute(_EXISTING_FEATURES, {"plan_id": plan_id})
    except SQLAlchemyError as exc:  # pragma: no cover - defensive
        raise EntitlementLoaderError(str(exc)) from exc
    records = result.mappings().all()
    existing: dict[str, dict[str, object]] = {}
    for record in records:
        existing[str(record["feature_key"])]= {
            "id": record["id"],
            "display_name": record.get("display_name"),
            "hard_limit": record.get("hard_limit"),
            "soft_limit": record.get("soft_limit"),
            "is_metered": bool(record.get("is_metered", False)),
        }
    return existing


def _needs_update(row: Mapping[str, object], payload: Mapping[str, object]) -> bool:
    return any(
        row.get(field) != payload[field]
        for field in ("display_name", "hard_limit", "soft_limit", "is_metered")
    )


def _load_artifact(path: Path) -> _ArtifactModel:
    if not path.exists():
        raise EntitlementLoaderError(f"Entitlement artifact not found at {path}.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EntitlementLoaderError(f"Unable to parse artifact JSON: {exc}") from exc
    try:
        return _ArtifactModel.model_validate(payload)
    except ValidationError as exc:  # pragma: no cover - defensive
        raise EntitlementLoaderError(str(exc)) from exc


__all__ = [
    "EntitlementLoaderError",
    "PlanSyncResult",
    "UsageEntitlementSyncResult",
    "sync_usage_entitlements",
]
