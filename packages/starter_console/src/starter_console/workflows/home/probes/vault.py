from __future__ import annotations

import os

import httpx

from starter_console.core.status_models import ProbeResult
from starter_console.workflows.home.probes.util import simple_result


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

    ok, detail, status = _vault_ping(addr, token, timeout=1.5)
    return simple_result(
        name="vault",
        success=ok,
        warn_on_failure=warn_only,
        detail=detail,
        remediation="Verify VAULT_ADDR is reachable and token has sys/health access.",
        metadata={"status": status},
    )


def _vault_ping(addr: str, token: str, *, timeout: float = 1.5) -> tuple[bool, str, int | None]:
    url = addr.rstrip("/") + "/v1/sys/health"
    headers = {"X-Vault-Token": token}
    try:
        resp = httpx.get(url, headers=headers, timeout=timeout)
        status = resp.status_code
        # Vault returns different codes for sealed/standby; treat non-5xx as reachable.
        if status in {200, 204}:
            return True, "unsealed", status
        if status in {429, 472, 473, 501, 503}:
            return False, f"vault reachable but state={status}", status
        if status == 403:
            return False, "vault auth failed (403)", status
        return False, f"vault responded {status}", status
    except httpx.HTTPError as exc:  # pragma: no cover - via monkeypatch
        return False, f"http_error: {exc}", None


__all__ = ["vault_probe"]
