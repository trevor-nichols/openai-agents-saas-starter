"""Manual streaming check for reasoning summary events.

Run locally only (opt-in):

    pytest tests/manual/test_reasoning_summary_manual.py -m manual --run-manual --asyncio-mode=auto

Reasoning summary emission depends on model settings. If no reasoning summary
events appear, the test skips.
"""

from __future__ import annotations

import json
import os
from getpass import getpass
from pathlib import Path

import httpx
import pytest

from app.api.v1.shared.streaming import PublicSseEvent, PublicSseEventBase, ReasoningSummaryDeltaEvent
from tests.utils.stream_assertions import assert_reasoning_summary_expectations, maybe_record_stream


def _default_base_url() -> str:
    api_env = os.getenv("NEXT_PUBLIC_API_URL")
    if api_env:
        return api_env
    port = os.getenv("PORT", "8000")
    return f"http://localhost:{port}"


async def _login_dev_user(
    base_url: str, timeout: float, *, email: str, password: str
) -> tuple[str, str]:
    url = f"{base_url.rstrip('/')}/api/v1/auth/token"
    payload = {"email": email, "password": password, "tenant_id": None}
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            pytest.skip(f"Dev login failed: {resp.status_code} {resp.text}")
        data = resp.json()
        return data["access_token"], data["tenant_id"]


@pytest.mark.manual
@pytest.mark.asyncio
async def test_reasoning_summary_streaming_manual() -> None:
    base_url = _default_base_url()
    timeout = float(os.getenv("MANUAL_TIMEOUT", "60"))

    token = os.getenv("MANUAL_ACCESS_TOKEN")
    tenant_id = os.getenv("MANUAL_TENANT_ID")
    if not token or not tenant_id:
        email = os.getenv("DEV_USER_EMAIL", "dev@example.com")
        password = os.getenv("DEV_USER_PASSWORD") or getpass(f"Password for {email}: ")
        token, tenant_id = await _login_dev_user(base_url, timeout, email=email, password=password)

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": tenant_id,
        "X-Tenant-Role": "owner",
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }

    payload = {
        "agent_type": os.getenv("MANUAL_AGENT", "triage"),
        "message": os.getenv(
            "MANUAL_MESSAGE",
            "You are given 3 containers with capacities 3, 5, and 8 liters. "
            "Explain how to measure exactly 4 liters using the fewest steps.",
        ),
    }

    url = f"{base_url.rstrip('/')}/api/v1/chat/stream"
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            body = (await resp.aread()).decode("utf-8", "ignore")
            assert resp.status_code == 200, f"status {resp.status_code}: {body}"

            events: list[PublicSseEventBase] = []
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                try:
                    event = json.loads(line[5:].lstrip())
                except json.JSONDecodeError:
                    continue

                parsed = PublicSseEvent.model_validate(event).root
                events.append(parsed)

                if getattr(parsed, "kind", None) in {"final", "error"}:
                    break

    if not any(isinstance(e, ReasoningSummaryDeltaEvent) for e in events):
        pytest.skip("No reasoning summary events observed for this run.")

    assert_reasoning_summary_expectations(events)

    repo_root = Path(__file__).resolve().parents[4]
    default_path = (
        repo_root
        / "docs"
        / "contracts"
        / "public-sse-streaming"
        / "examples"
        / "chat-reasoning-summary.ndjson"
    )
    maybe_record_stream(events, env_var="MANUAL_RECORD_STREAM_TO", default_path=default_path)

