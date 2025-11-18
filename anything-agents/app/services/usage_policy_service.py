"""Plan-aware usage policy enforcement and caching."""
from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Protocol

from redis.asyncio import Redis

from app.core.settings.usage import SoftLimitMode, UsageGuardrailCacheBackend
from app.domain.billing import PlanFeature, UsageTotal
from app.services.billing.billing_service import (
    BillingService,
    PlanNotFoundError,
    SubscriptionNotFoundError,
)

logger = logging.getLogger(__name__)


class UsagePolicyError(Exception):
    """Base error for usage policy evaluation issues."""


class UsagePolicyConfigurationError(UsagePolicyError):
    """Raised when enforcing policies without the necessary plan/subscription info."""


class UsagePolicyUnavailableError(UsagePolicyError):
    """Raised when backing stores (e.g., usage repository) are unavailable."""


class UsagePolicyDecision(str, Enum):
    ALLOW = "allow"
    SOFT_LIMIT = "soft_limit"
    HARD_LIMIT = "hard_limit"


@dataclass(slots=True)
class UsageViolation:
    feature_key: str
    limit_type: str
    limit_value: int
    usage: int
    unit: str
    window_start: datetime
    window_end: datetime


@dataclass(slots=True)
class UsagePolicyResult:
    decision: UsagePolicyDecision
    window_start: datetime
    window_end: datetime
    plan_code: str | None = None
    violations: list[UsageViolation] = field(default_factory=list)
    warnings: list[UsageViolation] = field(default_factory=list)


class UsageTotalsCache(Protocol):
    async def get(self, key: str) -> list[UsageTotal] | None: ...

    async def set(self, key: str, totals: Sequence[UsageTotal]) -> None: ...


class InMemoryUsageTotalsCache(UsageTotalsCache):
    """Simple thread-safe cache for usage rollups with TTL invalidation."""

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = max(0, ttl_seconds)
        self._store: dict[str, tuple[float, list[UsageTotal]]] = {}
        self._lock = threading.Lock()

    async def get(self, key: str) -> list[UsageTotal] | None:
        if self._ttl <= 0:
            return None
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, payload = entry
            if expires_at < time.time():
                self._store.pop(key, None)
                return None
            snapshot = [_clone_total(item) for item in payload]
        return snapshot

    async def set(self, key: str, totals: Sequence[UsageTotal]) -> None:
        if self._ttl <= 0:
            return
        snapshot = [_clone_total(item) for item in totals]
        with self._lock:
            self._store[key] = (time.time() + self._ttl, snapshot)


class RedisUsageTotalsCache(UsageTotalsCache):
    """Redis-backed cache for usage totals shared across API instances."""

    def __init__(
        self,
        redis: Redis[bytes],
        ttl_seconds: int,
        *,
        prefix: str = "usage_totals",
    ) -> None:
        self._redis = redis
        self._ttl = max(0, ttl_seconds)
        self._prefix = prefix.rstrip(":")

    async def get(self, key: str) -> list[UsageTotal] | None:
        if self._ttl <= 0:
            return None
        raw = await self._redis.get(self._encode_key(key))
        if raw is None:
            return None
        try:
            payload = json.loads(raw)
        except (TypeError, json.JSONDecodeError):  # pragma: no cover - defensive
            return None
        return [
            UsageTotal(
                feature_key=item["feature_key"],
                unit=item["unit"],
                quantity=int(item["quantity"]),
                window_start=_parse_datetime(item["window_start"]),
                window_end=_parse_datetime(item["window_end"]),
            )
            for item in payload
        ]

    async def set(self, key: str, totals: Sequence[UsageTotal]) -> None:
        if self._ttl <= 0:
            return
        serialized = json.dumps([
            {
                "feature_key": total.feature_key,
                "unit": total.unit,
                "quantity": total.quantity,
                "window_start": total.window_start.isoformat(),
                "window_end": total.window_end.isoformat(),
            }
            for total in totals
        ])
        await self._redis.set(self._encode_key(key), serialized, ex=self._ttl)

    def _encode_key(self, key: str) -> str:
        return f"{self._prefix}:{key}"


@dataclass(slots=True)
class UsagePolicyService:
    billing_service: BillingService
    cache: UsageTotalsCache | None = None
    soft_limit_mode: SoftLimitMode = "warn"

    async def evaluate(self, tenant_id: str) -> UsagePolicyResult:
        subscription = await self._require_subscription(tenant_id)
        plan = await self._require_plan(subscription.plan_code)
        monitored_features = self._monitored_features(plan.features)
        window_start = _normalize_datetime(
            subscription.current_period_start or subscription.starts_at
        )
        window_end = _normalize_datetime(subscription.current_period_end)
        now = datetime.now(UTC)
        window_start = window_start or now
        window_end = window_end or now

        if not monitored_features:
            return UsagePolicyResult(
                decision=UsagePolicyDecision.ALLOW,
                window_start=window_start,
                window_end=window_end,
                plan_code=plan.code,
            )

        feature_keys = [feature.key for feature in monitored_features]
        totals = await self._load_usage_totals(
            tenant_id,
            feature_keys=feature_keys,
            period_start=window_start,
            period_end=window_end,
        )
        totals_map = {total.feature_key: total for total in totals}

        hard_hits: list[UsageViolation] = []
        soft_hits: list[UsageViolation] = []

        for feature in monitored_features:
            total = totals_map.get(feature.key)
            used = total.quantity if total else 0
            unit = total.unit if total else "units"
            feature_window_start = total.window_start if total else window_start
            feature_window_end = total.window_end if total else window_end

            if feature.hard_limit is not None and used >= feature.hard_limit:
                hard_hits.append(
                    UsageViolation(
                        feature_key=feature.key,
                        limit_type="hard_limit",
                        limit_value=feature.hard_limit,
                        usage=used,
                        unit=unit,
                        window_start=feature_window_start,
                        window_end=feature_window_end,
                    )
                )
            elif feature.soft_limit is not None and used >= feature.soft_limit:
                soft_hits.append(
                    UsageViolation(
                        feature_key=feature.key,
                        limit_type="soft_limit",
                        limit_value=feature.soft_limit,
                        usage=used,
                        unit=unit,
                        window_start=feature_window_start,
                        window_end=feature_window_end,
                    )
                )

        if hard_hits:
            return UsagePolicyResult(
                decision=UsagePolicyDecision.HARD_LIMIT,
                window_start=window_start,
                window_end=window_end,
                plan_code=plan.code,
                violations=hard_hits,
            )

        if soft_hits:
            decision = (
                UsagePolicyDecision.HARD_LIMIT
                if self.soft_limit_mode == "block"
                else UsagePolicyDecision.SOFT_LIMIT
            )
            if decision is UsagePolicyDecision.HARD_LIMIT:
                return UsagePolicyResult(
                    decision=decision,
                    window_start=window_start,
                    window_end=window_end,
                    plan_code=plan.code,
                    violations=soft_hits,
                )
            return UsagePolicyResult(
                decision=decision,
                window_start=window_start,
                window_end=window_end,
                plan_code=plan.code,
                warnings=soft_hits,
            )

        return UsagePolicyResult(
            decision=UsagePolicyDecision.ALLOW,
            window_start=window_start,
            window_end=window_end,
            plan_code=plan.code,
        )

    async def _require_subscription(self, tenant_id: str):
        subscription = await self.billing_service.get_subscription(tenant_id)
        if not subscription:
            raise UsagePolicyConfigurationError(
                f"Tenant '{tenant_id}' does not have an active subscription."
            )
        return subscription

    async def _require_plan(self, plan_code: str):
        try:
            return await self.billing_service.get_plan(plan_code)
        except PlanNotFoundError as exc:
            raise UsagePolicyConfigurationError(
                f"Plan '{plan_code}' is not defined; cannot enforce usage guardrails."
            ) from exc

    def _monitored_features(self, features: Sequence[PlanFeature]) -> list[PlanFeature]:
        monitored: list[PlanFeature] = []
        for feature in features:
            if not feature.is_metered:
                continue
            if feature.hard_limit is None and feature.soft_limit is None:
                continue
            monitored.append(feature)
        return monitored

    async def _load_usage_totals(
        self,
        tenant_id: str,
        *,
        feature_keys: list[str],
        period_start: datetime,
        period_end: datetime,
    ) -> list[UsageTotal]:
        cache_key = self._cache_key(tenant_id, feature_keys, period_start, period_end)
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return cached
        try:
            totals = await self.billing_service.get_usage_totals(
                tenant_id,
                feature_keys=feature_keys,
                period_start=period_start,
                period_end=period_end,
            )
        except SubscriptionNotFoundError as exc:
            raise UsagePolicyConfigurationError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - repository edge cases
            raise UsagePolicyUnavailableError("Failed to load usage rollups.") from exc
        if self.cache:
            await self.cache.set(cache_key, totals)
        return totals

    def _cache_key(
        self,
        tenant_id: str,
        feature_keys: list[str],
        period_start: datetime,
        period_end: datetime,
    ) -> str:
        ordered_keys = ",".join(sorted(feature_keys))
        return f"{tenant_id}:{period_start.isoformat()}:{period_end.isoformat()}:{ordered_keys}"


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _clone_total(total: UsageTotal) -> UsageTotal:
    return UsageTotal(
        feature_key=total.feature_key,
        unit=total.unit,
        quantity=total.quantity,
        window_start=total.window_start,
        window_end=total.window_end,
    )


def build_usage_policy_service(
    *,
    billing_service: BillingService,
    cache_ttl_seconds: int,
    soft_limit_mode: SoftLimitMode,
    cache_backend: UsageGuardrailCacheBackend = "memory",
    redis_client: Redis[bytes] | None = None,
) -> UsagePolicyService:
    cache: UsageTotalsCache | None = None
    if cache_ttl_seconds > 0:
        if cache_backend == "redis":
            if redis_client is None:
                raise ValueError("Redis client required when cache backend is set to 'redis'.")
            cache = RedisUsageTotalsCache(redis_client, cache_ttl_seconds)
        else:
            cache = InMemoryUsageTotalsCache(cache_ttl_seconds)
    return UsagePolicyService(
        billing_service=billing_service,
        cache=cache,
        soft_limit_mode=soft_limit_mode,
    )


def get_usage_policy_service() -> UsagePolicyService | None:
    from app.bootstrap.container import get_container

    container = get_container()
    return container.usage_policy_service


__all__ = [
    "UsagePolicyDecision",
    "UsagePolicyResult",
    "UsagePolicyService",
    "UsagePolicyUnavailableError",
    "UsagePolicyConfigurationError",
    "UsageViolation",
    "RedisUsageTotalsCache",
    "build_usage_policy_service",
    "get_usage_policy_service",
]
