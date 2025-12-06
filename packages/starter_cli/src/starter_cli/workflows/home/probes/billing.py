from __future__ import annotations

from starter_cli.core.constants import TRUE_LITERALS
from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home.probes.registry import ProbeContext
from starter_cli.workflows.home.probes.stripe import stripe_probe


def billing_probe(ctx: ProbeContext) -> ProbeResult:
    enabled = _is_truthy(ctx.env.get("ENABLE_BILLING"))
    key = ctx.env.get("STRIPE_SECRET_KEY")

    if not enabled and not key:
        return ProbeResult(
            name="billing",
            state=ProbeState.SKIPPED,
            detail="billing disabled",
            metadata={"provider": "stripe", "reason": "not enabled"},
        )

    if not key:
        return ProbeResult(
            name="billing",
            state=ProbeState.WARN if ctx.warn_only else ProbeState.ERROR,
            detail="STRIPE_SECRET_KEY missing",
            remediation="Set STRIPE_SECRET_KEY or disable billing (ENABLE_BILLING=false).",
            metadata={"provider": "stripe"},
        )

    stripe_result = stripe_probe(warn_only=ctx.warn_only)
    return ProbeResult(
        name="billing",
        state=stripe_result.state,
        detail=stripe_result.detail,
        remediation=stripe_result.remediation,
        duration_ms=stripe_result.duration_ms,
        metadata={**dict(stripe_result.metadata), "provider": "stripe"},
        created_at=stripe_result.created_at,
    )


def _is_truthy(raw: str | None) -> bool:
    if raw is None:
        return False
    return raw.lower() in TRUE_LITERALS


__all__ = ["billing_probe"]
