from __future__ import annotations

import os
from urllib.parse import urljoin

from starter_cli.core.status_models import ProbeResult
from starter_cli.workflows.home.probes.util import http_check, simple_result


def frontend_probe(*, warn_only: bool = False) -> ProbeResult:
    base = os.getenv("APP_PUBLIC_URL") or "http://localhost:3000"
    url = urljoin(base.rstrip("/") + "/", "api/health/ready")
    ok, detail, status = http_check(url)
    if not ok:
        fallback = urljoin(base.rstrip("/") + "/", "health/ready")
        ok, detail, status = http_check(fallback)
        url = fallback

    return simple_result(
        name="frontend",
        success=ok,
        warn_on_failure=warn_only,
        detail=detail,
        remediation="Start the Next.js app (pnpm dev) or fix APP_PUBLIC_URL.",
        metadata={"url": url, "status": status},
    )


__all__ = ["frontend_probe"]
