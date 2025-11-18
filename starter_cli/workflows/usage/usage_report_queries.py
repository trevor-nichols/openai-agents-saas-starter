"""Database access helpers for usage reporting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Iterable, Sequence

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from starter_cli.workflows.usage.usage_report_models import UsageReportRequest


class UsageReportQueryError(Exception):
    """Raised when a SQL query fails."""


@dataclass(slots=True)
class SubscriptionRow:
    subscription_id: str
    tenant_id: str
    tenant_slug: str
    tenant_name: str | None
    plan_id: str
    plan_code: str
    plan_name: str
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None


@dataclass(slots=True)
class PlanFeatureRow:
    plan_code: str
    feature_key: str
    display_name: str | None
    soft_limit: int | None
    hard_limit: int | None
    is_metered: bool


@dataclass(slots=True)
class UsageRow:
    subscription_id: str
    feature_key: str
    unit: str
    quantity: int
    period_start: datetime
    period_end: datetime


async def fetch_subscriptions(
    connection: AsyncConnection,
    request: UsageReportRequest,
) -> list[SubscriptionRow]:
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if not request.include_inactive:
        clauses.append("ts.status = 'active'")

    if request.tenant_slugs:
        clause, clause_params = _build_in_clause("ta.slug", request.tenant_slugs, "tenant")
        clauses.append(clause)
        params.update(clause_params)

    if request.plan_codes:
        clause, clause_params = _build_in_clause("bp.code", request.plan_codes, "plan")
        clauses.append(clause)
        params.update(clause_params)

    where = " AND ".join(["1=1", *clauses])
    query = text(
        f"""
        SELECT
            ts.id AS subscription_id,
            ts.tenant_id,
            ta.slug AS tenant_slug,
            ta.name AS tenant_name,
            ts.plan_id,
            bp.code AS plan_code,
            bp.name AS plan_name,
            ts.status,
            ts.current_period_start,
            ts.current_period_end
        FROM tenant_subscriptions ts
        JOIN tenant_accounts ta ON ts.tenant_id = ta.id
        JOIN billing_plans bp ON ts.plan_id = bp.id
        WHERE {where}
        ORDER BY ta.slug, bp.code
        """
    )

    try:
        result = await connection.execute(query, params)
    except SQLAlchemyError as exc:  # pragma: no cover - defensive
        raise UsageReportQueryError(f"Failed to query subscriptions: {exc}") from exc

    rows: list[SubscriptionRow] = []
    for row in result:
        mapping = row._mapping if hasattr(row, "_mapping") else row
        rows.append(
            SubscriptionRow(
                subscription_id=str(mapping["subscription_id"]),
                tenant_id=str(mapping["tenant_id"]),
                tenant_slug=str(mapping["tenant_slug"]),
                tenant_name=str(mapping.get("tenant_name")) if mapping.get("tenant_name") else None,
                plan_id=str(mapping["plan_id"]),
                plan_code=str(mapping["plan_code"]),
                plan_name=str(mapping["plan_name"]),
                status=str(mapping["status"]),
                current_period_start=_ensure_datetime(mapping.get("current_period_start")),
                current_period_end=_ensure_datetime(mapping.get("current_period_end")),
            )
        )
    return rows


async def fetch_plan_features(
    connection: AsyncConnection,
    plan_codes: Iterable[str],
    feature_filter: Sequence[str] | None,
) -> dict[str, dict[str, PlanFeatureRow]]:
    plan_list = sorted(set(plan_codes))
    if not plan_list:
        return {}

    clauses = ["pf.is_metered = TRUE"]
    params: dict[str, Any] = {}

    clause, clause_params = _build_in_clause("bp.code", plan_list, "feature_plan")
    clauses.append(clause)
    params.update(clause_params)

    if feature_filter:
        clause, clause_params = _build_in_clause("pf.feature_key", feature_filter, "feature")
        clauses.append(clause)
        params.update(clause_params)

    where = " AND ".join(clauses)
    query = text(
        f"""
        SELECT
            bp.code AS plan_code,
            pf.feature_key,
            pf.display_name,
            pf.soft_limit,
            pf.hard_limit,
            pf.is_metered
        FROM plan_features pf
        JOIN billing_plans bp ON pf.plan_id = bp.id
        WHERE {where}
        ORDER BY bp.code, pf.feature_key
        """
    )

    try:
        result = await connection.execute(query, params)
    except SQLAlchemyError as exc:  # pragma: no cover - defensive
        raise UsageReportQueryError(f"Failed to query plan features: {exc}") from exc

    features: dict[str, dict[str, PlanFeatureRow]] = {}
    for row in result:
        mapping = row._mapping if hasattr(row, "_mapping") else row
        plan_code = str(mapping["plan_code"])
        feature_key = str(mapping["feature_key"])
        plan_features = features.setdefault(plan_code, {})
        plan_features[feature_key] = PlanFeatureRow(
            plan_code=plan_code,
            feature_key=feature_key,
            display_name=mapping.get("display_name"),
            soft_limit=_safe_int(mapping.get("soft_limit")),
            hard_limit=_safe_int(mapping.get("hard_limit")),
            is_metered=bool(mapping.get("is_metered", True)),
        )
    return features


async def fetch_usage_rows(
    connection: AsyncConnection,
    subscription_ids: Sequence[str],
    feature_filter: Sequence[str] | None,
    period_start: datetime | None,
    period_end: datetime | None,
) -> list[UsageRow]:
    if not subscription_ids:
        return []

    clauses = ["1=1"]
    params: dict[str, Any] = {}

    clause, clause_params = _build_in_clause("subscription_id", subscription_ids, "usage_sub")
    clauses.append(clause)
    params.update(clause_params)

    if feature_filter:
        clause, clause_params = _build_in_clause("feature_key", feature_filter, "usage_feature")
        clauses.append(clause)
        params.update(clause_params)

    if period_start is not None:
        clauses.append("period_end >= :global_period_start")
        params["global_period_start"] = period_start
    if period_end is not None:
        clauses.append("period_start <= :global_period_end")
        params["global_period_end"] = period_end

    where = " AND ".join(clauses)
    query = text(
        f"""
        SELECT subscription_id, feature_key, unit, quantity, period_start, period_end
        FROM subscription_usage
        WHERE {where}
        ORDER BY subscription_id, feature_key
        """
    )

    try:
        result = await connection.execute(query, params)
    except SQLAlchemyError as exc:  # pragma: no cover - defensive
        raise UsageReportQueryError(f"Failed to query usage records: {exc}") from exc

    rows: list[UsageRow] = []
    for row in result:
        mapping = row._mapping if hasattr(row, "_mapping") else row
        rows.append(
            UsageRow(
                subscription_id=str(mapping["subscription_id"]),
                feature_key=str(mapping["feature_key"]),
                unit=str(mapping.get("unit") or "units"),
                quantity=int(mapping.get("quantity", 0)),
                period_start=_ensure_datetime(mapping["period_start"]),
                period_end=_ensure_datetime(mapping["period_end"]),
            )
        )
    return rows


def _build_in_clause(column: str, values: Iterable[str], prefix: str) -> tuple[str, dict[str, Any]]:
    placeholders: list[str] = []
    params: dict[str, Any] = {}
    for index, value in enumerate(values):
        key = f"{prefix}_{index}"
        placeholders.append(f":{key}")
        params[key] = value
    if not placeholders:
        return "1=1", {}
    return f"{column} IN ({', '.join(placeholders)})", params


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return None


def _ensure_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        text_value = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text_value)
        except ValueError:  # pragma: no cover - defensive
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


__all__ = [
    "UsageReportQueryError",
    "SubscriptionRow",
    "PlanFeatureRow",
    "UsageRow",
    "fetch_subscriptions",
    "fetch_plan_features",
    "fetch_usage_rows",
]
