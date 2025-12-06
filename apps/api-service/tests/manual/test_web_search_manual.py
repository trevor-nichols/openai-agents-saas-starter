"""Manual streaming check for the hosted web_search tool.

Run locally only, opt-in:

    pytest tests/manual/test_web_search_manual.py -m manual --run-manual --asyncio-mode=auto

Auth strategy:
- If MANUAL_ACCESS_TOKEN and MANUAL_TENANT_ID are set, use them.
- Otherwise prompt once for the dev user's password (default email dev@example.com) and log in.

Base URL:
- Use NEXT_PUBLIC_API_URL if set; else http://localhost:{PORT or 8000}.

This test is skipped in CI by default via the `manual` marker and --run-manual flag.
"""

from __future__ import annotations

import json
import os
from getpass import getpass
from pathlib import Path

import httpx
import pytest

from app.api.v1.shared.streaming import StreamingEvent
from tests.utils.stream_assertions import (
    assert_web_search_expectations,
    maybe_record_stream,
)


def _default_base_url() -> str:
    api_env = os.getenv("NEXT_PUBLIC_API_URL")
    if api_env:
        return api_env
    port = os.getenv("PORT", "8000")
    return f"http://localhost:{port}"


async def _login_dev_user(base_url: str, timeout: float, *, email: str, password: str) -> tuple[str, str]:
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
async def test_web_search_streaming_manual() -> None:
    base_url = _default_base_url()
    timeout = float(os.getenv("MANUAL_TIMEOUT", "45"))

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
        "agent_type": "researcher",
        "message": os.getenv(
            "MANUAL_MESSAGE",
            "Use web search to find one positive news headline from today. Cite the URL."
            " You must perform a web search before answering.",
        ),
        "share_location": True,
    }

    url = f"{base_url.rstrip('/')}/api/v1/chat/stream"
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            body = (await resp.aread()).decode("utf-8", "ignore")
            assert resp.status_code == 200, f"status {resp.status_code}: {body}"

            events: list[StreamingEvent] = []

            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                try:
                    event = json.loads(line[5:].lstrip())
                except json.JSONDecodeError:
                    continue

                parsed = StreamingEvent.model_validate(event)
                events.append(parsed)

                if event.get("is_terminal"):
                    break

    assert_web_search_expectations(events)

    default_path = Path(__file__).resolve().parent.parent / "fixtures" / "streams" / "web_search.ndjson"
    maybe_record_stream(events, env_var="MANUAL_RECORD_STREAM_TO", default_path=default_path)
