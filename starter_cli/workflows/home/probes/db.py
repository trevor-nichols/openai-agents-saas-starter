from __future__ import annotations

import os
from urllib.parse import urlparse

from starter_cli.core.status_models import ProbeResult
from starter_cli.workflows.home.probes.util import simple_result, tcp_check


def db_probe() -> ProbeResult:
    url = os.getenv("DATABASE_URL")
    if not url:
        return simple_result(
            name="database",
            success=False,
            warn_on_failure=False,
            detail="DATABASE_URL not set",
            remediation="Populate DATABASE_URL via setup wizard or env file.",
        )

    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    ok, detail = tcp_check(host, port)
    return simple_result(
        name="database",
        success=ok,
        detail=detail,
        remediation="Ensure Postgres is running and reachable at DATABASE_URL.",
        metadata={"host": host, "port": port},
    )


__all__ = ["db_probe"]
