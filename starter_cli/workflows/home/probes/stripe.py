from __future__ import annotations

import os
from typing import Tuple

import httpx

from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home.probes.util import simple_result

STRIPE_API_BASE = "https://api.stripe.com/v1/"


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

    ok, detail, status = _stripe_ping(key, timeout=1.5)
    if ok:
        return ProbeResult(
            name="stripe",
            state=ProbeState.OK,
            detail=detail,
            metadata={"status": status},
        )

    return simple_result(
        name="stripe",
        success=False,
        warn_on_failure=warn_only,
        detail=detail or "Stripe ping failed",
        remediation="Verify STRIPE_SECRET_KEY and network egress; retry.",
        metadata={"status": status},
    )


def _stripe_ping(secret_key: str, *, timeout: float = 1.5) -> Tuple[bool, str, int | None]:
    """Minimal auth check against Stripe balance endpoint."""

    try:
        resp = httpx.get(
            STRIPE_API_BASE + "balance",
            timeout=timeout,
            auth=(secret_key, ""),
            headers={"User-Agent": "starter-cli-doctor/1.0"},
        )
        status = resp.status_code
        if status == 200:
            return True, "balance ok", status
        if status == 401:
            return False, "Stripe authentication failed (401)", status
        return False, f"Stripe responded {status}", status
    except httpx.HTTPError as exc:  # pragma: no cover - covered via monkeypatch
        return False, f"http_error: {exc}", None


def SimpleInvalidKeyResult(warn_only: bool) -> ProbeResult:
    return simple_result(
        name="stripe",
        success=False,
        warn_on_failure=warn_only,
        detail="STRIPE_SECRET_KEY format looks invalid",
        remediation="Verify Stripe key (sk_test_*/sk_live_*) or environment selection.",
    )


__all__ = ["stripe_probe"]
