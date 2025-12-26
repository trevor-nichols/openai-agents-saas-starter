from __future__ import annotations

import os
from urllib.parse import urlparse

from starter_console.core.status_models import ProbeResult
from starter_console.workflows.home.probes.util import simple_result, tcp_check


def ports_probe() -> ProbeResult:
    api_url = os.getenv("API_BASE_URL") or "http://localhost:8000"
    fe_url = os.getenv("APP_PUBLIC_URL") or "http://localhost:3000"
    api_parsed = urlparse(api_url)
    fe_parsed = urlparse(fe_url)
    checks = []
    for label, parsed in (("api", api_parsed), ("frontend", fe_parsed)):
        host = parsed.hostname or "localhost"
        port = parsed.port or (8000 if label == "api" else 3000)
        ok, detail = tcp_check(host, port, timeout=0.5)
        checks.append((label, ok, detail, host, port))

    failing = [c for c in checks if not c[1]]
    success = not failing
    detail = ", ".join(
        f"{label}:{host}:{port}={'up' if ok else 'down'}"
        for label, ok, detail, host, port in checks
    )
    remediation = (
        None if success else "Start the missing service or adjust API_BASE_URL/APP_PUBLIC_URL."
    )
    metadata = {
        label: {"host": host, "port": port, "detail": detail}
        for label, ok, detail, host, port in checks
    }
    return simple_result(
        name="ports",
        success=success,
        warn_on_failure=True,
        detail=detail,
        remediation=remediation,
        metadata=metadata,
    )


__all__ = ["ports_probe"]
