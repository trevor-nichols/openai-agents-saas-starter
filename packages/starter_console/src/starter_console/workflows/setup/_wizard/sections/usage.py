"""Usage guardrail prompts for the setup wizard."""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from starter_console.core import CLIError

from ...inputs import InputProvider, is_headless_provider
from ...validators import parse_non_negative_int, validate_plan_map
from ..context import WizardContext


@dataclass(frozen=True)
class UsageDimension:
    key: str
    label: str
    unit: str


def default_dimensions() -> tuple[UsageDimension, ...]:
    return (
        UsageDimension("messages", "Messages", "requests"),
        UsageDimension("input_tokens", "Input tokens", "tokens"),
        UsageDimension("output_tokens", "Output tokens", "tokens"),
    )


_USAGE_DIMENSIONS: Final = default_dimensions()

_PLAN_PRESETS: Final[dict[str, dict[str, tuple[int | None, int | None]]]] = {
    "starter": {
        "messages": (150, 200),
        "input_tokens": (200_000, 250_000),
        "output_tokens": (75_000, 100_000),
    },
    "pro": {
        "messages": (1_000, 1_500),
        "input_tokens": (1_000_000, 1_500_000),
        "output_tokens": (400_000, 600_000),
    },
}

_ARTIFACT_FILENAME = "usage-entitlements.json"


@dataclass(slots=True)
class PlanLimit:
    soft: int | None = None
    hard: int | None = None


@dataclass(slots=True)
class PlanFeature:
    feature_key: str
    display_name: str
    unit: str
    is_metered: bool
    soft_limit: int | None
    hard_limit: int | None


@dataclass(slots=True)
class PlanEntitlement:
    plan_code: str
    features: list[PlanFeature]


def run(context: WizardContext, provider: InputProvider) -> None:
    context.console.section(
        "Usage & Entitlements",
        "Decide whether to enforce plan guardrails before chat execution "
        "and capture per-plan limits.",
    )
    if not context.current_bool("ENABLE_BILLING", False):
        context.console.warn(
            "Billing is disabled; usage guardrails require billing. Skipping this section.",
            topic="wizard",
        )
        _set_guardrail_flags(context, enabled=False)
        _write_entitlements_report(context, enabled=False, plans=_load_existing_plans(context))
        _record_skip(context, "ENABLE_USAGE_GUARDRAILS", "ENABLE_BILLING is false")
        return

    enabled = provider.prompt_bool(
        key="ENABLE_USAGE_GUARDRAILS",
        prompt="Enforce plan-aware usage guardrails before chat execution?",
        default=context.current_bool("ENABLE_USAGE_GUARDRAILS", False),
    )
    _set_guardrail_flags(context, enabled=enabled)
    _record_answer(context, "ENABLE_USAGE_GUARDRAILS", "true" if enabled else "false")

    existing = _load_existing_plans(context)
    if not enabled:
        context.console.info(
            "Usage guardrails disabled; existing entitlements retained for future runs.",
            topic="wizard",
        )
        _write_entitlements_report(context, enabled=False, plans=existing)
        return

    ttl = _prompt_cache_ttl(context, provider)
    mode = _prompt_soft_limit_mode(context, provider)
    context.set_backend("USAGE_GUARDRAIL_CACHE_TTL_SECONDS", str(ttl))
    context.set_backend("USAGE_GUARDRAIL_SOFT_LIMIT_MODE", mode)

    cache_backend = _prompt_cache_backend(context, provider)
    context.set_backend("USAGE_GUARDRAIL_CACHE_BACKEND", cache_backend)
    if cache_backend == "redis":
        redis_url = _prompt_usage_redis_url(context, provider)
        if redis_url:
            context.set_backend("USAGE_GUARDRAIL_REDIS_URL", redis_url)
        else:
            context.unset_backend("USAGE_GUARDRAIL_REDIS_URL")
    else:
        context.unset_backend("USAGE_GUARDRAIL_REDIS_URL")

    plan_codes = _prompt_plan_codes(context, provider, existing)
    entitlements = _collect_plan_entitlements(context, provider, plan_codes, existing)
    entitlements = _inject_vector_limits(context, entitlements)
    _write_entitlements_report(context, enabled=True, plans=entitlements)
    context.console.success(
        "Usage guardrails configured. Remember to seed plan features in Postgres before launch.",
        topic="wizard",
    )


def _set_guardrail_flags(context: WizardContext, *, enabled: bool) -> None:
    context.set_backend_bool("ENABLE_USAGE_GUARDRAILS", enabled)
    if not enabled:
        context.unset_backend("USAGE_GUARDRAIL_CACHE_BACKEND")
        context.unset_backend("USAGE_GUARDRAIL_REDIS_URL")
        return
    ttl_current = context.current("USAGE_GUARDRAIL_CACHE_TTL_SECONDS") or "30"
    mode_current = context.current("USAGE_GUARDRAIL_SOFT_LIMIT_MODE") or "warn"
    backend_current = context.current("USAGE_GUARDRAIL_CACHE_BACKEND") or "redis"
    context.set_backend("USAGE_GUARDRAIL_CACHE_TTL_SECONDS", ttl_current)
    context.set_backend("USAGE_GUARDRAIL_SOFT_LIMIT_MODE", mode_current)
    context.set_backend("USAGE_GUARDRAIL_CACHE_BACKEND", backend_current)


def _prompt_cache_ttl(context: WizardContext, provider: InputProvider) -> int:
    current = context.current("USAGE_GUARDRAIL_CACHE_TTL_SECONDS") or "30"
    while True:
        raw_value = provider.prompt_string(
            key="USAGE_GUARDRAIL_CACHE_TTL_SECONDS",
            prompt="Usage rollup cache TTL (seconds)",
            default=current,
            required=True,
        ).strip()
        try:
            ttl = parse_non_negative_int(
                raw_value,
                field="USAGE_GUARDRAIL_CACHE_TTL_SECONDS",
            )
        except CLIError as exc:
            if is_headless_provider(provider):
                raise
            context.console.warn(str(exc), topic="wizard")
            continue
        return ttl


def _prompt_soft_limit_mode(context: WizardContext, provider: InputProvider) -> str:
    current = context.current("USAGE_GUARDRAIL_SOFT_LIMIT_MODE") or "warn"
    default = current if current in {"warn", "block"} else "warn"
    while True:
        value = provider.prompt_string(
            key="USAGE_GUARDRAIL_SOFT_LIMIT_MODE",
            prompt="Soft limit behavior (warn/block)",
            default=default,
            required=True,
        ).strip().lower()
        if value in {"warn", "block"}:
            return value
        if is_headless_provider(provider):
            raise CLIError("USAGE_GUARDRAIL_SOFT_LIMIT_MODE must be 'warn' or 'block'.")
        context.console.warn("Enter either 'warn' or 'block'.", topic="wizard")


def _prompt_cache_backend(context: WizardContext, provider: InputProvider) -> str:
    current = context.current("USAGE_GUARDRAIL_CACHE_BACKEND") or "redis"
    default = current if current in {"redis", "memory"} else "redis"
    while True:
        value = (
            provider.prompt_string(
                key="USAGE_GUARDRAIL_CACHE_BACKEND",
                prompt="Usage cache backend (redis/memory)",
                default=default,
                required=True,
            )
            .strip()
            .lower()
        )
        if value in {"redis", "memory"}:
            _record_answer(context, "USAGE_GUARDRAIL_CACHE_BACKEND", value)
            return value
        if is_headless_provider(provider):
            raise CLIError("USAGE_GUARDRAIL_CACHE_BACKEND must be 'redis' or 'memory'.")
        context.console.warn("Enter either 'redis' or 'memory'.", topic="wizard")


def _prompt_usage_redis_url(context: WizardContext, provider: InputProvider) -> str | None:
    default = context.current("USAGE_GUARDRAIL_REDIS_URL") or context.current("REDIS_URL") or ""
    value = (
        provider.prompt_string(
            key="USAGE_GUARDRAIL_REDIS_URL",
            prompt="Usage guardrail Redis URL (blank to reuse REDIS_URL)",
            default=default,
            required=False,
        )
        .strip()
    )
    if not value:
        _record_skip(context, "USAGE_GUARDRAIL_REDIS_URL", "inherit REDIS_URL")
        return None
    _record_answer(context, "USAGE_GUARDRAIL_REDIS_URL", value)
    return value


def _prompt_plan_codes(
    context: WizardContext,
    provider: InputProvider,
    existing: list[PlanEntitlement],
) -> list[str]:
    default_codes = _derive_default_plan_codes(context, existing)
    default_value = ",".join(default_codes)
    raw = provider.prompt_string(
        key="USAGE_PLAN_CODES",
        prompt="Plan codes to configure (comma separated)",
        default=default_value or "starter,pro",
        required=True,
    )
    codes = [code.strip().lower() for code in raw.split(",") if code.strip()]
    if not codes:
        raise CLIError("At least one plan code must be provided for usage guardrails.")
    _record_answer(context, "USAGE_PLAN_CODES", ",".join(codes))
    seen: set[str] = set()
    ordered: list[str] = []
    for code in codes:
        if code in seen:
            continue
        seen.add(code)
        ordered.append(code)
    return ordered


def _derive_default_plan_codes(
    context: WizardContext, existing: list[PlanEntitlement]
) -> list[str]:
    if existing:
        return [plan.plan_code for plan in existing]
    plan_map_raw = context.current("STRIPE_PRODUCT_PRICE_MAP")
    if plan_map_raw:
        try:
            plan_map = validate_plan_map(plan_map_raw)
        except CLIError as exc:
            context.console.warn(
                f"Unable to parse STRIPE_PRODUCT_PRICE_MAP for plan codes: {exc}",
                topic="wizard",
            )
        else:
            if plan_map:
                return list(plan_map.keys())
    return ["starter", "pro"]


def _collect_plan_entitlements(
    context: WizardContext,
    provider: InputProvider,
    plan_codes: list[str],
    existing: list[PlanEntitlement],
) -> list[PlanEntitlement]:
    existing_lookup = _as_lookup(existing)
    entitlements: list[PlanEntitlement] = []
    for code in plan_codes:
        features: list[PlanFeature] = []
        for dimension in _USAGE_DIMENSIONS:
            preset = _resolve_limit_defaults(code, dimension.key, existing_lookup)
            soft = _prompt_limit(
                context,
                provider,
                plan_code=code,
                dimension=dimension,
                limit_type="soft",
                default=preset.soft,
            )
            hard = _prompt_limit(
                context,
                provider,
                plan_code=code,
                dimension=dimension,
                limit_type="hard",
                default=preset.hard,
            )
            features.append(
                PlanFeature(
                    feature_key=dimension.key,
                    display_name=dimension.label,
                    unit=dimension.unit,
                    is_metered=True,
                    soft_limit=soft,
                    hard_limit=hard,
                )
            )
        entitlements.append(PlanEntitlement(plan_code=code, features=features))
    return entitlements


def _inject_vector_limits(
    context: WizardContext, entitlements: list[PlanEntitlement]
) -> list[PlanEntitlement]:
    # Align with backend defaults; operators can edit the artifact manually if needed.
    max_file_mb = int(context.current("VECTOR_MAX_FILE_MB") or 512)
    max_files_per_store = int(context.current("VECTOR_MAX_FILES_PER_STORE") or 5000)
    max_stores_per_tenant = int(context.current("VECTOR_MAX_STORES_PER_TENANT") or 10)
    max_total_bytes = _parse_total_bytes(context.current("VECTOR_MAX_TOTAL_BYTES"))

    vector_features = {
        "vector.max_file_bytes": max_file_mb * 1024 * 1024,
        "vector.files_per_store": max_files_per_store,
        "vector.stores_per_tenant": max_stores_per_tenant,
    }
    if max_total_bytes is not None:
        vector_features["vector.total_bytes_per_tenant"] = max_total_bytes

    updated: list[PlanEntitlement] = []
    for plan in entitlements:
        features_map = {f.feature_key: f for f in plan.features}
        for key, limit in vector_features.items():
            features_map[key] = PlanFeature(
                feature_key=key,
                display_name=key,
                unit="bytes" if "bytes" in key else "count",
                is_metered=False,
                soft_limit=None,
                hard_limit=limit,
            )
        updated.append(
            PlanEntitlement(
                plan_code=plan.plan_code,
                features=list(features_map.values()),
            )
        )
    return updated


def _parse_total_bytes(raw: str | None) -> int | None:
    """Return an int when raw is a number-like string; otherwise None."""
    if raw is None:
        return None
    if raw in {"", "null"}:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _prompt_limit(
    context: WizardContext,
    provider: InputProvider,
    *,
    plan_code: str,
    dimension: UsageDimension,
    limit_type: str,
    default: int | None,
) -> int | None:
    key = (
        f"USAGE_{plan_code.upper()}_{dimension.key.upper()}_{limit_type.upper()}_LIMIT"
    )
    prompt = (
        f"{plan_code} {dimension.label} {limit_type} limit ({dimension.unit}); blank to disable"
    )
    default_str = "" if default is None else str(default)
    while True:
        raw = provider.prompt_string(
            key=key,
            prompt=prompt,
            default=default_str,
            required=False,
        ).strip()
        if not raw:
            _record_skip(context, key, "blank")
            return None
        try:
            value = parse_non_negative_int(raw, field=key)
        except CLIError as exc:
            if is_headless_provider(provider):
                raise
            context.console.warn(str(exc), topic="wizard")
            continue
        _record_answer(context, key, str(value))
        return value


def _resolve_limit_defaults(
    plan_code: str,
    feature_key: str,
    existing: Mapping[str, Mapping[str, PlanLimit]],
) -> PlanLimit:
    plan_key = plan_code.lower()
    existing_plan = existing.get(plan_key)
    if existing_plan:
        stored = existing_plan.get(feature_key)
        if stored:
            return stored
    preset_plan = _PLAN_PRESETS.get(plan_key)
    if preset_plan and feature_key in preset_plan:
        soft, hard = preset_plan[feature_key]
        return PlanLimit(soft=soft, hard=hard)
    return PlanLimit()


def _usage_report_path(context: WizardContext) -> Path:
    reports_dir = context.cli_ctx.project_root / "var/reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir / _ARTIFACT_FILENAME


def _write_entitlements_report(
    context: WizardContext,
    *,
    enabled: bool,
    plans: list[PlanEntitlement],
) -> None:
    path = _usage_report_path(context)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "enabled": enabled,
        "plans": [
            {
                "plan_code": plan.plan_code,
                "features": [
                    {
                        "feature_key": feature.feature_key,
                        "display_name": feature.display_name,
                        "unit": feature.unit,
                        "is_metered": feature.is_metered,
                        "soft_limit": feature.soft_limit,
                        "hard_limit": feature.hard_limit,
                    }
                    for feature in plan.features
                ],
            }
            for plan in plans
        ],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rel_path = _relative_to_project(context, path)
    context.console.info(f"Wrote {rel_path} with plan entitlements.", topic="wizard")


def _relative_to_project(context: WizardContext, path: Path) -> str:
    try:
        return str(path.relative_to(context.cli_ctx.project_root))
    except ValueError:  # pragma: no cover - fallback
        return str(path)


def _load_existing_plans(context: WizardContext) -> list[PlanEntitlement]:
    path = _usage_report_path(context)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    plans_data = payload.get("plans")
    if not isinstance(plans_data, list):
        return []
    entitlements: list[PlanEntitlement] = []
    for item in plans_data:
        plan_code = item.get("plan_code")
        features = item.get("features", [])
        if not isinstance(plan_code, str) or not isinstance(features, list):
            continue
        parsed_features: list[PlanFeature] = []
        for feature in features:
            if not isinstance(feature, dict):
                continue
            feature_key = feature.get("feature_key")
            display_name = feature.get("display_name") or feature_key or "feature"
            unit = feature.get("unit") or "units"
            soft = feature.get("soft_limit")
            hard = feature.get("hard_limit")
            parsed_features.append(
                PlanFeature(
                    feature_key=str(feature_key),
                    display_name=str(display_name),
                    unit=str(unit),
                    is_metered=bool(feature.get("is_metered", True)),
                    soft_limit=int(soft) if isinstance(soft, int) else None,
                    hard_limit=int(hard) if isinstance(hard, int) else None,
                )
            )
        entitlements.append(PlanEntitlement(plan_code=str(plan_code), features=parsed_features))
    return entitlements


def _as_lookup(
    entitlements: list[PlanEntitlement],
) -> Mapping[str, Mapping[str, PlanLimit]]:
    lookup: dict[str, dict[str, PlanLimit]] = {}
    for plan in entitlements:
        feature_map: dict[str, PlanLimit] = {}
        for feature in plan.features:
            feature_map[feature.feature_key] = PlanLimit(
                soft=feature.soft_limit,
                hard=feature.hard_limit,
            )
        lookup[plan.plan_code.lower()] = feature_map
    return lookup


def _record_answer(context: WizardContext, key: str, value: str) -> None:
    if context.state_store:
        context.state_store.record_answer(key, value)


def _record_skip(context: WizardContext, key: str, reason: str) -> None:
    if context.state_store:
        context.state_store.record_skip(key, reason)


__all__ = ["run"]
