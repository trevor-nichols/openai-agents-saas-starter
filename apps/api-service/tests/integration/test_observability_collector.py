from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx
import pytest

from app.core.settings import Settings
from app.observability.logging import configure_logging, log_event

COLLECTOR_IMAGE = "otel/opentelemetry-collector-contrib:0.139.0"
# tests live under apps/api-service/tests/**, so repo root is four levels up
REPO_ROOT = Path(__file__).resolve().parents[4]
RENDER_SCRIPT = REPO_ROOT / "ops" / "observability" / "render_collector_config.py"


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_health(port: int, timeout: float = 20.0) -> None:
    url = f"http://127.0.0.1:{port}/healthz"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = httpx.get(url, timeout=1.0)
            if resp.status_code == 200:
                return
        except Exception:  # pragma: no cover - transient startup failures
            pass
        time.sleep(0.5)
    raise AssertionError("Collector health endpoint did not become ready")


def _wait_for_log(container: str, needle: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        logs = subprocess.run(
            ["docker", "logs", container],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
        ).stdout
        if needle in logs:
            return
        time.sleep(0.5)
    logs = subprocess.run(
        ["docker", "logs", container],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    ).stdout
    raise AssertionError(f"Collector logs never emitted '{needle}'.\nLogs:\n{logs}")


@pytest.mark.integration
def test_bundled_collector_receives_backend_logs(tmp_path):
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI is required for the collector smoke test.")

    config_path = tmp_path / "collector.yaml"
    env = os.environ | {
        "ENABLE_OTEL_COLLECTOR": "true",
        "OTEL_COLLECTOR_CONFIG_PATH": str(config_path),
        "OTEL_DEBUG_VERBOSITY": "detailed",
    }
    subprocess.run(
        [sys.executable, str(RENDER_SCRIPT)], env=env, check=True
    )
    assert config_path.exists(), "Collector config was not generated"

    container_name = f"collector-smoke-{uuid.uuid4().hex[:8]}"
    host_http_port = _find_free_port()
    host_diag_port = _find_free_port()

    # Skip cleanly when Docker is installed but the daemon is not running
    try:
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pytest.skip("Docker daemon is not running; skipping collector smoke test.")

    run_cmd = [
        "docker",
        "run",
        "-d",
        "--rm",
        "--name",
        container_name,
        "-p",
        f"{host_http_port}:4318",
        "-p",
        f"{host_diag_port}:13133",
        "-v",
        f"{config_path}:/etc/otelcol-contrib/config.yaml:ro",
        COLLECTOR_IMAGE,
    ]
    subprocess.run(run_cmd, check=True)
    try:
        _wait_for_health(host_diag_port)
        settings = Settings.model_validate(
            {
                "APP_NAME": "collector-smoke",
                "ENVIRONMENT": "test",
                # Override local .env.local defaults (LOGGING_SINKS=stdout,file) for this test.
                "LOGGING_SINKS": "otlp",
                "LOGGING_SINK": "otlp",
                "LOGGING_OTLP_ENDPOINT": f"http://127.0.0.1:{host_http_port}/v1/logs",
            }
        )
        configure_logging(settings)
        event_token = f"collector-smoke-{uuid.uuid4().hex}"
        log_event("collector.smoke", message=event_token, token=event_token)
        _wait_for_log(container_name, event_token)
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
