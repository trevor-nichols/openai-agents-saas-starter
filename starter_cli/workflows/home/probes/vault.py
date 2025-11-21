from __future__ import annotations

import os

from starter_cli.core.status_models import ProbeResult
from starter_cli.workflows.home.probes.util import simple_result


def vault_probe(*, warn_only: bool) -> ProbeResult:
    addr = os.getenv("VAULT_ADDR")
    token = os.getenv("VAULT_TOKEN")
    if not addr:
        return simple_result(
            name="vault",
            success=False,
            warn_on_failure=warn_only,
            detail="VAULT_ADDR not set",
            remediation="Export VAULT_ADDR/VAULT_TOKEN or choose a secrets provider in the wizard.",
        )

    if not token:
        return simple_result(
            name="vault",
            success=False,
            warn_on_failure=warn_only,
            detail="VAULT_TOKEN not set",
            remediation="Provide a token with transit:verify for CLI operations.",
        )

    return simple_result(
        name="vault",
        success=True,
        detail="addr/token present (connectivity not probed)",
    )


__all__ = ["vault_probe"]
