"""FastAPI dependencies for usage guardrail enforcement."""
from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, status

from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.core.settings import get_settings
from app.observability import metrics as observability_metrics
from app.services.usage.policy_service import (
    UsagePolicyConfigurationError,
    UsagePolicyDecision,
    UsagePolicyResult,
    UsagePolicyService,
    UsagePolicyUnavailableError,
    UsageViolation,
    get_usage_policy_service,
)

logger = logging.getLogger(__name__)


async def enforce_usage_guardrails(
    tenant_context: TenantContext = Depends(
        require_tenant_role(TenantRole.VIEWER, TenantRole.ADMIN, TenantRole.OWNER)
    ),
    usage_policy_service: UsagePolicyService | None = Depends(get_usage_policy_service),
) -> UsagePolicyResult | None:
    settings = get_settings()
    if not settings.enable_usage_guardrails:
        return None

    if usage_policy_service is None:
        logger.warning(
            "Usage guardrails enabled but UsagePolicyService is not configured.",
            extra={"tenant_id": tenant_context.tenant_id},
        )
        return None

    try:
        result = await usage_policy_service.evaluate(tenant_context.tenant_id)
    except UsagePolicyConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "usage_policy_configuration_error",
                "message": str(exc),
                "tenant_id": tenant_context.tenant_id,
            },
        ) from exc
    except UsagePolicyUnavailableError as exc:
        logger.warning(
            "Usage policy evaluation unavailable; allowing request.",
            extra={"tenant_id": tenant_context.tenant_id},
            exc_info=exc,
        )
        return None

    _record_guardrail_metrics(result)

    if result.decision is UsagePolicyDecision.HARD_LIMIT:
        violation = _pick_violation(result)
        logger.error(
            "Tenant exceeded hard usage limit; blocking request.",
            extra=_violation_payload(
                "usage_limit_exceeded",
                violation,
                tenant_context.tenant_id,
                result.plan_code,
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=_violation_payload(
                "usage_limit_exceeded",
                violation,
                tenant_context.tenant_id,
                result.plan_code,
            ),
        )

    if result.decision is UsagePolicyDecision.SOFT_LIMIT:
        for violation in result.warnings:
            logger.warning(
                "Tenant exceeded soft usage limit.",
                extra=_violation_payload(
                    "usage_soft_limit_exceeded",
                    violation,
                    tenant_context.tenant_id,
                    result.plan_code,
                ),
            )
    return result


def _record_guardrail_metrics(result: UsagePolicyResult) -> None:
    observability_metrics.record_usage_guardrail_decision(
        decision=result.decision.value,
        plan_code=result.plan_code,
    )
    for violation in result.violations:
        observability_metrics.record_usage_limit_hit(
            plan_code=result.plan_code,
            limit_type=violation.limit_type,
            feature_key=violation.feature_key,
        )
    for warning in result.warnings:
        observability_metrics.record_usage_limit_hit(
            plan_code=result.plan_code,
            limit_type=warning.limit_type,
            feature_key=warning.feature_key,
        )


def _pick_violation(result: UsagePolicyResult) -> UsageViolation:
    if result.violations:
        return result.violations[0]
    if result.warnings:
        return result.warnings[0]
    raise RuntimeError("UsagePolicyResult did not contain violation details.")


def _violation_payload(
    code: str,
    violation: UsageViolation,
    tenant_id: str | None = None,
    plan_code: str | None = None,
) -> dict[str, object]:
    return {
        "code": code,
        "tenant_id": tenant_id,
        "plan_code": plan_code,
        "feature_key": violation.feature_key,
        "limit_type": violation.limit_type,
        "limit_value": violation.limit_value,
        "usage": violation.usage,
        "unit": violation.unit,
        "window_start": violation.window_start.isoformat(),
        "window_end": violation.window_end.isoformat(),
    }


__all__ = ["enforce_usage_guardrails"]
