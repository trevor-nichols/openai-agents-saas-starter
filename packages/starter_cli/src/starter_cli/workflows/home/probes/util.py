from __future__ import annotations

import socket
from collections.abc import Callable, Iterable
from time import perf_counter
from typing import Any

import httpx

from starter_cli.core.status_models import ProbeResult, ProbeState


def time_call(func: Callable[[], Any]) -> tuple[Any, float]:
    """Run ``func`` and return (result, duration_ms)."""

    start = perf_counter()
    result = func()
    duration_ms = (perf_counter() - start) * 1000
    return result, duration_ms


def tcp_check(host: str, port: int, *, timeout: float = 1.5) -> tuple[bool, str]:
    """Attempt a TCP connection to host:port.

    Returns (success, detail). Never raises.
    """

    def _dial() -> tuple[bool, str]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            code = sock.connect_ex((host, port))
            if code == 0:
                return True, "connected"
            return False, f"connect_ex={code}"

    try:
        return _dial()
    except OSError as exc:  # pragma: no cover - defensive
        return False, f"oserror: {exc}"


def http_check(
    url: str,
    *,
    timeout: float = 2.0,
    expected_status: Iterable[int] = (200, 204),
) -> tuple[bool, str, int | None]:
    """Perform a lightweight HTTP GET.

    Returns (success, detail, status_code). Never raises.
    """

    status: int | None = None
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=False)
        status = resp.status_code
        ok = status in set(expected_status)
        detail = "ok" if ok else f"status={status}"
        return ok, detail, status
    except httpx.HTTPError as exc:
        return False, f"http_error: {exc}"[:200], status


def guard_probe(
    name: str,
    func: Callable[[], ProbeResult],
    *,
    default_state: ProbeState = ProbeState.ERROR,
    remediation: str | None = None,
    force_skip: bool = False,
    skip_reason: str | None = None,
) -> ProbeResult:
    """Execute a probe, converting exceptions into a ProbeResult.

    Keeps probe execution resilient so one failure does not abort the doctor run.
    """

    if force_skip:
        return ProbeResult(
            name=name,
            state=ProbeState.SKIPPED,
            detail=skip_reason or "skipped",
            remediation=remediation,
        )

    try:
        result, duration_ms = time_call(func)
    except Exception as exc:  # pragma: no cover - exercised implicitly
        return ProbeResult(
            name=name,
            state=default_state,
            detail=f"unhandled exception: {exc}",
            remediation=remediation,
        )

    if isinstance(result, ProbeResult):
        # Respect the probe's own timing only if not set.
        if result.duration_ms is None:
            result = ProbeResult(
                name=result.name,
                state=result.state,
                detail=result.detail,
                remediation=result.remediation,
                duration_ms=duration_ms,
                metadata=result.metadata,
            )
        return result

    raise TypeError(  # pragma: no cover - defensive
        f"Probe '{name}' must return ProbeResult, got {type(result)!r}"
    )


def simple_result(
    *,
    name: str,
    success: bool,
    detail: str | None = None,
    remediation: str | None = None,
    warn_on_failure: bool = False,
    duration_ms: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProbeResult:
    """Helper to build a ProbeResult from a boolean outcome."""

    state = ProbeState.OK if success else (ProbeState.WARN if warn_on_failure else ProbeState.ERROR)
    return ProbeResult(
        name=name,
        state=state,
        detail=detail,
        remediation=remediation,
        duration_ms=duration_ms,
        metadata=metadata or {},
    )


__all__ = [
    "guard_probe",
    "http_check",
    "simple_result",
    "tcp_check",
    "time_call",
]
