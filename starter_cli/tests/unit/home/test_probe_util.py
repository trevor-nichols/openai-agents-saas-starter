from __future__ import annotations

import http.server
import socket
import threading
import time

from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home.probes.util import (
    guard_probe,
    http_check,
    simple_result,
    tcp_check,
    time_call,
)


class _OKHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format: str, *args):  # pragma: no cover - quiet server
        return


def _start_http_server() -> tuple[threading.Thread, int, http.server.ThreadingHTTPServer]:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _OKHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread, port, server


def test_time_call_measures_duration():
    def _work():
        time.sleep(0.01)
        return "done"

    result, duration_ms = time_call(_work)
    assert result == "done"
    assert duration_ms >= 10


def test_tcp_check_success_and_failure():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        ok, detail = tcp_check("127.0.0.1", port, timeout=0.5)
        assert ok is True
        assert detail == "connected"

    ok, detail = tcp_check("127.0.0.1", port, timeout=0.2)
    assert ok is False
    assert "connect_ex" in detail


def test_http_check_success_and_http_error():
    thread, port, server = _start_http_server()
    try:
        ok, detail, status = http_check(f"http://127.0.0.1:{port}", timeout=1.0)
        assert ok is True
        assert detail == "ok"
        assert status == 200
    finally:
        server.shutdown()
        thread.join(timeout=1)

    ok, detail, status = http_check("http://127.0.0.1:9", timeout=0.2)
    assert ok is False
    assert "http_error" in detail
    assert status is None


def test_guard_probe_wraps_exceptions_and_sets_duration():
    def ok_probe() -> ProbeResult:
        return ProbeResult(name="ok", state=ProbeState.OK, detail="fine")

    result = guard_probe("ok", ok_probe)
    assert result.state is ProbeState.OK
    assert result.duration_ms is not None

    def bad_probe() -> ProbeResult:  # pragma: no cover - tested via guard
        raise RuntimeError("boom")

    result = guard_probe("bad", bad_probe)
    assert result.state is ProbeState.ERROR
    assert "unhandled" in (result.detail or "")


def test_simple_result_warns_when_configured():
    warn_result = simple_result(
        name="stripe",
        success=False,
        warn_on_failure=True,
        detail="skipped in local",
    )
    assert warn_result.state is ProbeState.WARN
    error_result = simple_result(name="db", success=False)
    assert error_result.state is ProbeState.ERROR
