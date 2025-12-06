from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from starter_cli.workflows.usage.entitlement_loader import (
    EntitlementLoaderError,
    sync_usage_entitlements,
)


@pytest.mark.asyncio
async def test_sync_entitlements_upserts_features(tmp_path):
    database_url = _sqlite_url(tmp_path, "usage.db")
    await _bootstrap_schema(database_url)
    await _insert_plan(database_url, code="starter")

    artifact_path = tmp_path / "usage-entitlements.json"
    artifact_path.write_text(
        json.dumps(
            {
                "enabled": True,
                "generated_at": datetime.now(UTC).isoformat(),
                "plans": [
                    {
                        "plan_code": "starter",
                        "features": [
                            {
                                "feature_key": "messages",
                                "display_name": "Messages",
                                "unit": "requests",
                                "soft_limit": 80,
                                "hard_limit": 120,
                                "is_metered": True,
                            },
                            {
                                "feature_key": "input_tokens",
                                "display_name": "Input Tokens",
                                "unit": "tokens",
                                "soft_limit": 100000,
                                "hard_limit": 150000,
                                "is_metered": True,
                            },
                            {
                                "feature_key": "output_tokens",
                                "display_name": "Output Tokens",
                                "unit": "tokens",
                                "soft_limit": 40000,
                                "hard_limit": 60000,
                                "is_metered": True,
                            },
                        ],
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = await sync_usage_entitlements(
        database_url=database_url,
        artifact_path=artifact_path,
        plan_filter=None,
        prune_missing=False,
        dry_run=False,
        allow_disabled_artifact=False,
    )

    assert result.plan_results[0].inserted == 3
    features = await _fetch_features(database_url)
    assert features["messages"]["hard_limit"] == 120

    # Update artifact to change a limit and ensure we issue an update.
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["plans"][0]["features"][0]["hard_limit"] = 130
    artifact_path.write_text(json.dumps(artifact) + "\n", encoding="utf-8")

    update_result = await sync_usage_entitlements(
        database_url=database_url,
        artifact_path=artifact_path,
        plan_filter=None,
        prune_missing=False,
        dry_run=False,
        allow_disabled_artifact=False,
    )
    assert update_result.plan_results[0].updated == 1
    features = await _fetch_features(database_url)
    assert features["messages"]["hard_limit"] == 130


@pytest.mark.asyncio
async def test_sync_entitlements_prunes_missing_features(tmp_path):
    database_url = _sqlite_url(tmp_path, "usage-prune.db")
    await _bootstrap_schema(database_url)
    await _insert_plan(database_url, code="pro")

    artifact_path = tmp_path / "usage-entitlements.json"
    artifact = {
        "enabled": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "plans": [
            {
                "plan_code": "pro",
                "features": [
                    {
                        "feature_key": "messages",
                        "display_name": "Messages",
                        "unit": "requests",
                        "soft_limit": 100,
                        "hard_limit": 150,
                        "is_metered": True,
                    },
                    {
                        "feature_key": "input_tokens",
                        "display_name": "Input Tokens",
                        "unit": "tokens",
                        "soft_limit": 200000,
                        "hard_limit": 250000,
                        "is_metered": True,
                    },
                ],
            }
        ],
    }
    artifact_path.write_text(json.dumps(artifact) + "\n", encoding="utf-8")
    await sync_usage_entitlements(
        database_url=database_url,
        artifact_path=artifact_path,
        plan_filter=None,
        prune_missing=False,
        dry_run=False,
        allow_disabled_artifact=False,
    )

    # Drop one feature and sync with prune enabled.
    artifact["plans"][0]["features"] = artifact["plans"][0]["features"][:1]
    artifact_path.write_text(json.dumps(artifact) + "\n", encoding="utf-8")
    result = await sync_usage_entitlements(
        database_url=database_url,
        artifact_path=artifact_path,
        plan_filter=None,
        prune_missing=True,
        dry_run=False,
        allow_disabled_artifact=False,
    )

    assert result.plan_results[0].pruned == 1
    features = await _fetch_features(database_url)
    assert set(features.keys()) == {"messages"}


@pytest.mark.asyncio
async def test_sync_entitlements_rejects_disabled_artifact(tmp_path):
    database_url = _sqlite_url(tmp_path, "usage-disabled.db")
    await _bootstrap_schema(database_url)
    await _insert_plan(database_url, code="starter")

    artifact_path = tmp_path / "usage-entitlements.json"
    artifact_path.write_text(
        json.dumps({"enabled": False, "plans": []}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(EntitlementLoaderError):
        await sync_usage_entitlements(
            database_url=database_url,
            artifact_path=artifact_path,
            plan_filter=None,
            prune_missing=False,
            dry_run=False,
            allow_disabled_artifact=False,
        )


async def _bootstrap_schema(database_url: str) -> None:
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS billing_plans (
                        id TEXT PRIMARY KEY,
                        code TEXT NOT NULL,
                        name TEXT NOT NULL,
                        interval TEXT,
                        interval_count INTEGER,
                        price_cents INTEGER,
                        currency TEXT,
                        is_active INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS plan_features (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id TEXT NOT NULL,
                        feature_key TEXT NOT NULL,
                        display_name TEXT,
                        description TEXT,
                        hard_limit INTEGER,
                        soft_limit INTEGER,
                        is_metered INTEGER,
                        UNIQUE(plan_id, feature_key)
                    )
                    """
                )
            )
    finally:
        await engine.dispose()


async def _insert_plan(database_url: str, *, code: str) -> None:
    engine = create_async_engine(database_url)
    plan_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    INSERT INTO billing_plans (
                        id,
                        code,
                        name,
                        interval,
                        interval_count,
                        price_cents,
                        currency,
                        is_active,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        :id,
                        :code,
                        :name,
                        'monthly',
                        1,
                        1000,
                        'USD',
                        1,
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                {
                    "id": plan_id,
                    "code": code,
                    "name": code.title(),
                    "created_at": now,
                    "updated_at": now,
                },
            )
    finally:
        await engine.dispose()


async def _fetch_features(database_url: str) -> dict[str, dict[str, int | bool]]:
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT feature_key, display_name, soft_limit, hard_limit, is_metered "
                    "FROM plan_features"
                )
            )
            rows = result.fetchall()
    finally:
        await engine.dispose()

    features: dict[str, dict[str, int | bool]] = {}
    for row in rows:
        mapping = row._mapping
        features[str(mapping["feature_key"])] = {
            "display_name": mapping["display_name"],
            "soft_limit": mapping["soft_limit"],
            "hard_limit": mapping["hard_limit"],
            "is_metered": bool(mapping["is_metered"]),
        }
    return features


def _sqlite_url(tmp_path, name: str) -> str:
    db_path = tmp_path / name
    return f"sqlite+aiosqlite:///{db_path}"
