from __future__ import annotations

import os

from starter_console.core.inventory import WIZARD_PROMPTED_ENV_VARS
from starter_console.core.status_models import ProbeResult
from starter_console.workflows.home.probes.util import simple_result


def env_coverage_probe() -> ProbeResult:
    total = len(WIZARD_PROMPTED_ENV_VARS)
    present = sum(1 for key in WIZARD_PROMPTED_ENV_VARS if os.getenv(key))
    coverage = present / total if total else 1.0
    missing = sorted(key for key in WIZARD_PROMPTED_ENV_VARS if not os.getenv(key))
    detail = f"{present}/{total} ({coverage:.0%}) prompt vars set"
    remediation = None
    warn = bool(missing)
    metadata = {"missing": missing, "coverage": coverage}
    return simple_result(
        name="environment",
        success=not warn,
        warn_on_failure=True,
        detail=detail,
        remediation=remediation,
        metadata=metadata,
    )


__all__ = ["env_coverage_probe"]
