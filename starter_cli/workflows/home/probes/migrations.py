from __future__ import annotations

from pathlib import Path

from starter_cli.core.constants import PROJECT_ROOT
from starter_cli.core.status_models import ProbeResult, ProbeState


def migrations_probe() -> ProbeResult:
    versions_dir = PROJECT_ROOT / "api-service" / "alembic" / "versions"
    if not versions_dir.exists():
        return ProbeResult(
            name="migrations",
            state=ProbeState.WARN,
            detail="alembic/versions missing",
            remediation="Verify repo checkout includes migrations or regenerate via alembic.",
        )

    return ProbeResult(
        name="migrations",
        state=ProbeState.SKIPPED,
        detail="DB head not checked (future: alembic current)",
    )


__all__ = ["migrations_probe"]
