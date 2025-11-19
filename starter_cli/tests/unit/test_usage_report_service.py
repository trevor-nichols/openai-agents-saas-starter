from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from starter_cli.workflows.usage import UsageReportRequest
from starter_cli.workflows.usage.usage_report_models import UsageReport
from starter_cli.workflows.usage.usage_report_service import (
    UsageReportError,
    UsageReportService,
    write_usage_report_files,
)


@pytest.mark.asyncio
async def test_generate_report_builds_snapshots(tmp_path):
    database_url = _sqlite_url(tmp_path / "usage-report.db")
    _bootstrap_schema(database_url)

    tenant_id = str(uuid.uuid4())
    plan_id = str(uuid.uuid4())
    subscription_id = str(uuid.uuid4())
    now = datetime.now(UTC)

    _insert(
        database_url,
        "tenant_accounts",
        {
            "id": tenant_id,
            "slug": "acme",
            "name": "Acme Corp",
        },
    )
    _insert(
        database_url,
        "billing_plans",
        {
            "id": plan_id,
            "code": "starter",
            "name": "Starter",
            "interval": "monthly",
            "interval_count": 1,
            "price_cents": 5000,
            "currency": "USD",
            "is_active": 1,
        },
    )
    _insert(
        database_url,
        "plan_features",
        {
            "plan_id": plan_id,
            "feature_key": "messages",
            "display_name": "Messages",
            "soft_limit": 60,
            "hard_limit": 100,
            "is_metered": 1,
        },
    )
    _insert(
        database_url,
        "plan_features",
        {
            "plan_id": plan_id,
            "feature_key": "input_tokens",
            "display_name": "Input Tokens",
            "soft_limit": 1000,
            "hard_limit": 2000,
            "is_metered": 1,
        },
    )
    _insert(
        database_url,
        "tenant_subscriptions",
        {
            "id": subscription_id,
            "tenant_id": tenant_id,
            "plan_id": plan_id,
            "status": "active",
            "current_period_start": now.isoformat(),
            "current_period_end": (now + timedelta(days=28)).isoformat(),
        },
    )

    _insert(
        database_url,
        "subscription_usage",
        {
            "id": str(uuid.uuid4()),
            "subscription_id": subscription_id,
            "feature_key": "messages",
            "unit": "requests",
            "quantity": 55,
            "period_start": now.isoformat(),
            "period_end": now.isoformat(),
        },
    )
    _insert(
        database_url,
        "subscription_usage",
        {
            "id": str(uuid.uuid4()),
            "subscription_id": subscription_id,
            "feature_key": "input_tokens",
            "unit": "tokens",
            "quantity": 1500,
            "period_start": now.isoformat(),
            "period_end": now.isoformat(),
        },
    )

    service = UsageReportService()
    request = UsageReportRequest(
        database_url=database_url,
        tenant_slugs=("acme",),
        plan_codes=("starter",),
        warn_threshold=0.5,
    )
    report = await service.generate_report(request)

    assert report.tenant_filters == ("acme",)
    assert len(report.tenants) == 1
    tenant = report.tenants[0]
    assert tenant.tenant_slug == "acme"
    assert tenant.plan_code == "starter"
    feature_by_key = {feature.feature_key: feature for feature in tenant.features}
    assert feature_by_key["messages"].quantity == 55
    assert feature_by_key["messages"].status == "approaching"
    assert feature_by_key["messages"].approaching is True
    assert feature_by_key["input_tokens"].status == "soft_limit_exceeded"
    assert feature_by_key["input_tokens"].approaching is True


@pytest.mark.asyncio
async def test_generate_report_requires_matching_subscriptions(tmp_path):
    database_url = _sqlite_url(tmp_path / "usage-empty.db")
    _bootstrap_schema(database_url)
    service = UsageReportService()
    request = UsageReportRequest(database_url=database_url)
    with pytest.raises(UsageReportError):
        await service.generate_report(request)


def test_write_usage_report_files(tmp_path):
    dummy_report = UsageReport(
        generated_at=datetime.now(UTC),
        applied_period_start=None,
        applied_period_end=None,
        tenant_filters=(),
        plan_filters=(),
        feature_filters=(),
        warn_threshold=0.8,
        include_inactive=False,
        tenants=[],
    )
    artifacts = write_usage_report_files(
        dummy_report,
        json_path=tmp_path / "report.json",
        csv_path=tmp_path / "report.csv",
    )
    assert artifacts.json_path is not None
    assert artifacts.csv_path is not None
    assert artifacts.json_path.exists()
    assert artifacts.csv_path.exists()
    data = json.loads(artifacts.json_path.read_text(encoding="utf-8"))
    assert data["tenant_count"] == 0


def _sqlite_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path}"


def _bootstrap_schema(database_url: str) -> None:
    path = database_url.replace("sqlite+aiosqlite://", "")
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tenant_accounts (
                id TEXT PRIMARY KEY,
                slug TEXT NOT NULL,
                name TEXT
            );
            CREATE TABLE IF NOT EXISTS billing_plans (
                id TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                interval TEXT,
                interval_count INTEGER,
                price_cents INTEGER,
                currency TEXT,
                is_active INTEGER
            );
            CREATE TABLE IF NOT EXISTS plan_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT NOT NULL,
                feature_key TEXT NOT NULL,
                display_name TEXT,
                soft_limit INTEGER,
                hard_limit INTEGER,
                is_metered INTEGER
            );
            CREATE TABLE IF NOT EXISTS tenant_subscriptions (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                status TEXT,
                current_period_start TEXT,
                current_period_end TEXT
            );
            CREATE TABLE IF NOT EXISTS subscription_usage (
                id TEXT PRIMARY KEY,
                subscription_id TEXT NOT NULL,
                feature_key TEXT NOT NULL,
                unit TEXT,
                quantity INTEGER,
                period_start TEXT,
                period_end TEXT
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def _insert(database_url: str, table: str, values: dict[str, object]) -> None:
    path = database_url.replace("sqlite+aiosqlite://", "")
    conn = sqlite3.connect(path)
    try:
        columns = ",".join(values.keys())
        placeholders = ",".join(["?"] * len(values))
        conn.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )
        conn.commit()
    finally:
        conn.close()
