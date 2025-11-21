from __future__ import annotations

import os

from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home.probes.util import simple_result


def stripe_probe(*, warn_only: bool) -> ProbeResult:
    key = os.getenv("STRIPE_SECRET_KEY")
    if not key:
        return simple_result(
            name="stripe",
            success=False,
            warn_on_failure=warn_only,
            detail="STRIPE_SECRET_KEY missing",
            remediation="Run `python -m starter_cli.app stripe setup` or set STRIPE_SECRET_KEY.",
        )

    if not key.startswith(("sk_test_", "sk_live_")):
        return SimpleInvalidKeyResult(warn_only)

    return ProbeResult(name="stripe", state=ProbeState.OK, detail="key present")


def SimpleInvalidKeyResult(warn_only: bool) -> ProbeResult:
    return simple_result(
        name="stripe",
        success=False,
        warn_on_failure=warn_only,
        detail="STRIPE_SECRET_KEY format looks invalid",
        remediation="Verify Stripe key (sk_test_*/sk_live_*) or environment selection.",
    )


__all__ = ["stripe_probe"]
