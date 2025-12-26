"""Service object responsible for usage report generation."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from starter_console.workflows.usage.usage_report_models import (
    FeatureUsageSnapshot,
    TenantUsageSnapshot,
    UsageReport,
    UsageReportArtifacts,
    UsageReportRequest,
    write_report_csv,
    write_report_json,
)
from starter_console.workflows.usage.usage_report_queries import (
    PlanFeatureRow,
    SubscriptionRow,
    UsageReportQueryError,
    UsageRow,
    fetch_plan_features,
    fetch_subscriptions,
    fetch_usage_rows,
)


class UsageReportError(Exception):
    """Wraps query or transformation errors."""


EngineFactory = Callable[[str], AsyncEngine]


@dataclass(slots=True)
class TimeWindow:
    start: datetime | None
    end: datetime | None


@dataclass(slots=True)
class UsageAccumulator:
    quantity: int = 0
    unit: str = "units"
    window_start: datetime | None = None
    window_end: datetime | None = None

    def add(self, row: UsageRow) -> None:
        self.quantity += row.quantity
        self.unit = row.unit or self.unit
        self.window_start = _min_datetime(self.window_start, row.period_start)
        self.window_end = _max_datetime(self.window_end, row.period_end)


class UsageReportService:
    """Coordinates SQL queries and aggregations for CLI exports."""

    def __init__(self, engine_factory: EngineFactory | None = None) -> None:
        self._engine_factory = engine_factory or create_async_engine

    async def generate_report(self, request: UsageReportRequest) -> UsageReport:
        engine = self._engine_factory(request.database_url)
        try:
            async with engine.connect() as connection:
                subscriptions = await fetch_subscriptions(connection, request)
                if not subscriptions:
                    raise UsageReportError(
                        "No tenant subscriptions matched the provided filters."
                    )

                plan_features = await fetch_plan_features(
                    connection,
                    {row.plan_code for row in subscriptions},
                    request.feature_keys,
                )

                usage_rows = await fetch_usage_rows(
                    connection,
                    [row.subscription_id for row in subscriptions],
                    request.feature_keys,
                    request.period_start,
                    request.period_end,
                )
        except UsageReportQueryError as exc:
            raise UsageReportError(str(exc)) from exc
        finally:
            await engine.dispose()

        windows, derived_start, derived_end = self._compute_time_windows(subscriptions, request)
        usage_map = self._aggregate_usage(usage_rows, windows)
        tenants = self._build_tenant_snapshots(
            subscriptions,
            plan_features,
            usage_map,
            request,
            windows,
        )

        return UsageReport(
            generated_at=datetime.now(UTC),
            applied_period_start=derived_start,
            applied_period_end=derived_end,
            tenant_filters=request.tenant_slugs,
            plan_filters=request.plan_codes,
            feature_filters=request.feature_keys,
            warn_threshold=request.warn_threshold,
            include_inactive=request.include_inactive,
            tenants=tenants,
        )

    def _compute_time_windows(
        self,
        subscriptions: Sequence[SubscriptionRow],
        request: UsageReportRequest,
    ) -> tuple[dict[str, TimeWindow], datetime | None, datetime | None]:
        starts = [sub.current_period_start for sub in subscriptions if sub.current_period_start]
        ends = [sub.current_period_end for sub in subscriptions if sub.current_period_end]

        derived_start = request.period_start or _min_sequence(starts)
        derived_end = request.period_end or _max_sequence(ends)

        if derived_start and derived_end and derived_start > derived_end:
            derived_start, derived_end = derived_end, derived_start

        windows: dict[str, TimeWindow] = {}
        for sub in subscriptions:
            start = request.period_start or sub.current_period_start or derived_start
            end = request.period_end or sub.current_period_end or derived_end
            if start and end and start > end:
                start, end = end, start
            windows[sub.subscription_id] = TimeWindow(start=start, end=end)

        return windows, derived_start, derived_end

    def _aggregate_usage(
        self,
        usage_rows: Sequence[UsageRow],
        windows: dict[str, TimeWindow],
    ) -> dict[str, dict[str, UsageAccumulator]]:
        usage_map: dict[str, dict[str, UsageAccumulator]] = {}
        for row in usage_rows:
            window = windows.get(row.subscription_id)
            if window and not _overlaps(row.period_start, row.period_end, window.start, window.end):
                continue
            feature_map = usage_map.setdefault(row.subscription_id, {})
            accumulator = feature_map.setdefault(row.feature_key, UsageAccumulator())
            accumulator.add(row)
        return usage_map

    def _build_tenant_snapshots(
        self,
        subscriptions: Sequence[SubscriptionRow],
        plan_features: dict[str, dict[str, PlanFeatureRow]],
        usage_map: dict[str, dict[str, UsageAccumulator]],
        request: UsageReportRequest,
        windows: dict[str, TimeWindow],
    ) -> list[TenantUsageSnapshot]:
        feature_filter = set(request.feature_keys) if request.feature_keys else None
        warn_threshold = max(min(request.warn_threshold, 1.0), 0.0)

        tenants: list[TenantUsageSnapshot] = []
        for subscription in subscriptions:
            window = windows.get(subscription.subscription_id, TimeWindow(None, None))
            plan_definitions = plan_features.get(subscription.plan_code, {})
            usage_for_subscription = usage_map.get(subscription.subscription_id, {})

            feature_keys = set(plan_definitions.keys()) | set(usage_for_subscription.keys())
            if feature_filter:
                feature_keys &= feature_filter

            features = [
                self._build_feature_snapshot(
                    feature_key=feature_key,
                    definition=plan_definitions.get(feature_key),
                    accumulator=usage_for_subscription.get(feature_key),
                    warn_threshold=warn_threshold,
                )
                for feature_key in sorted(feature_keys)
            ]

            tenants.append(
                TenantUsageSnapshot(
                    tenant_id=subscription.tenant_id,
                    tenant_slug=subscription.tenant_slug,
                    tenant_name=subscription.tenant_name,
                    plan_code=subscription.plan_code,
                    plan_name=subscription.plan_name,
                    subscription_status=subscription.status,
                    window_start=window.start,
                    window_end=window.end,
                    features=features,
                )
            )

        return tenants

    def _build_feature_snapshot(
        self,
        *,
        feature_key: str,
        definition: PlanFeatureRow | None,
        accumulator: UsageAccumulator | None,
        warn_threshold: float,
    ) -> FeatureUsageSnapshot:
        quantity = accumulator.quantity if accumulator else 0
        unit = accumulator.unit if accumulator else "units"
        display_name = (definition.display_name if definition else None) or feature_key
        soft_limit = definition.soft_limit if definition else None
        hard_limit = definition.hard_limit if definition else None

        status = "ok"
        approaching = False
        if hard_limit is not None and quantity >= hard_limit:
            status = "hard_limit_exceeded"
            approaching = True
        elif soft_limit is not None and quantity >= soft_limit:
            status = "soft_limit_exceeded"
            approaching = True
        else:
            active_limit = soft_limit or hard_limit
            if active_limit:
                percent = quantity / active_limit
                approaching = percent >= warn_threshold
                if approaching:
                    status = "approaching"

        return FeatureUsageSnapshot(
            feature_key=feature_key,
            display_name=display_name,
            unit=unit,
            quantity=quantity,
            soft_limit=soft_limit,
            hard_limit=hard_limit,
            remaining_to_soft_limit=_remaining(soft_limit, quantity),
            remaining_to_hard_limit=_remaining(hard_limit, quantity),
            percent_of_soft_limit=_percent(quantity, soft_limit),
            percent_of_hard_limit=_percent(quantity, hard_limit),
            status=status,
            approaching=approaching,
            usage_window_start=(accumulator.window_start if accumulator else None),
            usage_window_end=(accumulator.window_end if accumulator else None),
        )


def write_usage_report_files(
    report: UsageReport,
    *,
    json_path: Path | None,
    csv_path: Path | None,
) -> UsageReportArtifacts:
    json_out = write_report_json(json_path, report) if json_path else None
    csv_out = write_report_csv(csv_path, report) if csv_path else None
    return UsageReportArtifacts(json_path=json_out, csv_path=csv_out)


def _remaining(limit_value: int | None, quantity: int) -> int | None:
    if limit_value is None:
        return None
    return max(limit_value - quantity, 0)


def _percent(quantity: int, limit_value: int | None) -> float | None:
    if limit_value is None or limit_value == 0:
        return None
    return round((quantity / limit_value) * 100, 2)


def _overlaps(
    record_start: datetime,
    record_end: datetime,
    window_start: datetime | None,
    window_end: datetime | None,
) -> bool:
    if window_start and record_end < window_start:
        return False
    if window_end and record_start > window_end:
        return False
    return True


def _min_datetime(current: datetime | None, candidate: datetime) -> datetime:
    if current is None:
        return candidate
    return candidate if candidate < current else current


def _max_datetime(current: datetime | None, candidate: datetime) -> datetime:
    if current is None:
        return candidate
    return candidate if candidate > current else current


def _min_sequence(values: Iterable[datetime]) -> datetime | None:
    iterator = iter(values)
    try:
        first = next(iterator)
    except StopIteration:
        return None
    minimum = first
    for value in iterator:
        minimum = _min_datetime(minimum, value)
    return minimum


def _max_sequence(values: Iterable[datetime]) -> datetime | None:
    iterator = iter(values)
    try:
        first = next(iterator)
    except StopIteration:
        return None
    maximum = first
    for value in iterator:
        maximum = _max_datetime(maximum, value)
    return maximum


__all__ = [
    "UsageReportService",
    "UsageReportError",
    "write_usage_report_files",
]
