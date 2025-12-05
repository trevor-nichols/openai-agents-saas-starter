"""Manual streaming check for the hosted code_interpreter tool.

Run locally only, opt-in:

    pytest tests/manual/test_code_interpreter_manual.py -m manual --run-manual --asyncio-mode=auto

Assertions:
- HTTP 200
- SSE events conform to StreamingEvent; terminal event present
- sequence_number monotonic; response_id stable
- code_interpreter_call status reaches completed
- At least one code_interpreter output recorded
- Assistant text is non-empty and references the computed result

Auth flow & base URL mirror the web search manual test: token if provided, otherwise prompt
for the dev password; NEXT_PUBLIC_API_URL/PORT for base URL.
"""

from __future__ import annotations

import json
import os
from getpass import getpass
from pathlib import Path

import httpx
import pytest

from app.api.v1.shared.streaming import ContainerFileCitation, StreamingEvent
from tests.utils.stream_assertions import (
    assert_code_interpreter_expectations,
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
async def test_code_interpreter_streaming_manual() -> None:
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
        "agent_type": "researcher",
        "message": (
            "Use the code interpreter to calculate the square root of 2 (or 2.0) using Python, "
            "show the numeric result, and ensure you run code before responding."
        ),
        "share_location": False,
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

    assert_code_interpreter_expectations(events)

    # Extra manual guards for container metadata & annotations on code interpreter calls.
    ci_calls = []
    for e in events:
        ci = None
        if isinstance(e.tool_call, dict):
            ci = e.tool_call.get("code_interpreter_call")
        elif e.tool_call:
            ci = getattr(e.tool_call, "code_interpreter_call", None)
        if ci:
            ci_calls.append(ci)

    assert ci_calls, "Expected at least one code_interpreter_call in stream"
    assert any(getattr(ci, "container_id", None) or (ci.get("container_id") if isinstance(ci, dict) else None) for ci in ci_calls), "Missing container_id on code_interpreter_call"
    assert all(
        (getattr(ci, "container_mode", None) or (ci.get("container_mode") if isinstance(ci, dict) else None))
        in {"auto", "explicit"}
        for ci in ci_calls
        if getattr(ci, "container_mode", None) or (ci.get("container_mode") if isinstance(ci, dict) else None)
    ), "container_mode should be auto or explicit"

    # If annotations were emitted, ensure we surface container_file_citation correctly.
    annotations_present = []
    for ci in ci_calls:
        anns = getattr(ci, "annotations", None) if not isinstance(ci, dict) else ci.get("annotations")
        if anns:
            annotations_present.extend(anns)
    if annotations_present:
        assert any(
            isinstance(a, ContainerFileCitation) or (isinstance(a, dict) and a.get("type") == "container_file_citation")
            for a in annotations_present
        ), "Expected container_file_citation in code_interpreter_call.annotations"

    default_path = Path(__file__).resolve().parent.parent / "fixtures" / "streams" / "code_interpreter.ndjson"
    maybe_record_stream(events, env_var="MANUAL_RECORD_STREAM_TO", default_path=default_path)
