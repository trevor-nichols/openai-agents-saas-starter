from __future__ import annotations

import json
import os
import socket
import time
import uuid
from pathlib import Path
from threading import Event, Thread
from typing import Any
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

from app.core.settings import Settings
from app.observability.logging import configure_logging, log_event

# tests live under apps/api-service/tests/**, so repo root is four levels up.
_ = Path(__file__).resolve().parents[4]

RECEIVE_TIMEOUT_SECONDS = float(os.getenv("STARTER_OTLP_RECEIVE_TIMEOUT_SECONDS", "10"))


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _ReceiverState:
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []
        self.received = Event()


def _start_otlp_http_receiver() -> tuple[_ReceiverState, ThreadingHTTPServer, Thread, str]:
    """Start a lightweight HTTP endpoint that mimics an OTLP/HTTP logs receiver.

    This keeps the integration test hermetic (no Docker dependency) while still exercising:
    `log_event(...)` -> JSON formatter -> OTLP conversion -> HTTP POST.
    """

    state = _ReceiverState()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 - stdlib naming
            if self.path != "/v1/logs":
                self.send_response(404)
                self.end_headers()
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            raw = self.rfile.read(length) if length else b""
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                return
            if isinstance(payload, dict):
                state.payloads.append(payload)
                state.received.set()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')

        def log_message(self, *_args: object, **_kwargs: object) -> None:
            return  # silence noisy stdlib request logs during pytest

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.timeout = 0.2
    url = f"http://127.0.0.1:{server.server_address[1]}/v1/logs"

    stop = Event()

    def run() -> None:
        # Avoid `server.shutdown()` deadlocks (it blocks unless `serve_forever()` is
        # already running in another thread). We control the loop explicitly so
        # teardown is always bounded.
        while not stop.is_set():
            server.handle_request()

    thread = Thread(target=run, name="otlp-http-receiver", daemon=True)
    thread.start()
    # attach stop signal for teardown (kept private to this module)
    setattr(server, "_stop_event", stop)
    return state, server, thread, url


def _payload_contains_token(payload: dict[str, Any], token: str) -> bool:
    # Be tolerant to schema shifts: search both OTLP "body" and attributes.
    try:
        resource_logs = payload.get("resourceLogs") or []
        for rl in resource_logs:
            scope_logs = (rl or {}).get("scopeLogs") or []
            for sl in scope_logs:
                records = (sl or {}).get("logRecords") or []
                for record in records:
                    body = (record or {}).get("body") or {}
                    if token in str(body):
                        return True
                    attrs = (record or {}).get("attributes") or []
                    for attr in attrs:
                        if token in str(attr):
                            return True
    except Exception:  # pragma: no cover - defensive
        return token in json.dumps(payload, sort_keys=True)
    return token in json.dumps(payload, sort_keys=True)


@pytest.mark.integration
def test_otlp_sink_posts_logs_over_http():
    state, server, thread, endpoint = _start_otlp_http_receiver()
    try:
        settings = Settings.model_validate(
            {
                "APP_NAME": "collector-smoke",
                "ENVIRONMENT": "test",
                # Override local .env.local defaults (LOGGING_SINKS=stdout,file) for this test.
                "LOGGING_SINKS": "otlp",
                "LOGGING_OTLP_ENDPOINT": endpoint,
            }
        )
        configure_logging(settings)
        event_token = f"collector-smoke-{uuid.uuid4().hex}"
        log_event("collector.smoke", message=event_token, token=event_token)
        deadline = time.time() + RECEIVE_TIMEOUT_SECONDS
        while time.time() < deadline and not state.received.is_set():
            time.sleep(0.05)
        assert state.payloads, "OTLP receiver did not capture any payloads"
        assert any(
            _payload_contains_token(payload, event_token) for payload in state.payloads
        ), "OTLP payload did not include emitted token"
    finally:
        stop = getattr(server, "_stop_event", None)
        if isinstance(stop, Event):
            stop.set()
        server.server_close()
        thread.join(timeout=1.0)
