from __future__ import annotations

import os
from urllib.parse import urlparse

from starter_cli.core.status_models import ProbeResult
from starter_cli.workflows.home.probes.util import simple_result, tcp_check


def redis_probe() -> ProbeResult:
    url = os.getenv("RATE_LIMIT_REDIS_URL") or os.getenv("REDIS_URL")
    if not url:
        return simple_result(
            name="redis",
            success=False,
            warn_on_failure=False,
            detail="REDIS_URL not set",
            remediation="Set REDIS_URL (or RATE_LIMIT_REDIS_URL) via wizard or env files.",
        )

    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    ok, detail = tcp_check(host, port)
    return simple_result(
        name="redis",
        success=ok,
        detail=detail,
        remediation="Ensure Redis is running and reachable at configured URL.",
        metadata={"host": host, "port": port},
    )


__all__ = ["redis_probe"]
