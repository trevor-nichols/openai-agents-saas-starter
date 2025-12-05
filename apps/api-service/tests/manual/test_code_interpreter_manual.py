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

import httpx
import pytest

from app.api.v1.shared.streaming import CodeInterpreterCall, StreamingEvent


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
        "agent_type": "code_assistant",
        "message": (
            "Use the code interpreter to compute the square root of 2, rounded to 3 decimals. "
            "You must execute Python code before responding. Show the numeric result and cite it." 
        ),
        "share_location": False,
    }

    url = f"{base_url.rstrip('/')}/api/v1/chat/stream"
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            body = (await resp.aread()).decode("utf-8", "ignore")
            assert resp.status_code == 200, f"status {resp.status_code}: {body}"

            events: list[StreamingEvent] = []
            assembled_text_parts: list[str] = []
            outputs_seen: list[CodeInterpreterCall] = []

            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                try:
                    event = json.loads(line[5:].lstrip())
                except json.JSONDecodeError:
                    continue

                parsed = StreamingEvent.model_validate(event)
                events.append(parsed)

                # Collect code interpreter status/outputs
                ci = None
                if isinstance(parsed.tool_call, dict):
                    ci = parsed.tool_call.get("code_interpreter_call")
                elif parsed.tool_call:
                    ci = getattr(parsed.tool_call, "code_interpreter_call", None)

                if ci:
                    status = ci.get("status") if isinstance(ci, dict) else getattr(ci, "status", None)
                    outputs = ci.get("outputs") if isinstance(ci, dict) else getattr(ci, "outputs", None)
                    if status == "completed":
                        outputs_seen.append(ci if isinstance(ci, CodeInterpreterCall) else CodeInterpreterCall(**ci))
                    if outputs:
                        outputs_seen.append(ci if isinstance(ci, CodeInterpreterCall) else CodeInterpreterCall(**ci))

                if parsed.text_delta:
                    assembled_text_parts.append(parsed.text_delta)

                if event.get("is_terminal"):
                    break

    # Structural assertions
    assert events, "Expected at least one streaming event"
    assert events[-1].is_terminal, "Stream must end with a terminal event"

    seqs = [e.sequence_number for e in events if e.sequence_number is not None]
    assert seqs == sorted(seqs), "sequence_number should be monotonically increasing"

    resp_ids = {e.response_id for e in events if e.response_id}
    assert len(resp_ids) <= 1, "response_id changed mid-stream"

    # Code interpreter must complete
    statuses = []
    for e in events:
        ci = None
        if isinstance(e.tool_call, dict):
            ci = e.tool_call.get("code_interpreter_call")
        elif e.tool_call:
            ci = getattr(e.tool_call, "code_interpreter_call", None)
        if ci:
            status = ci.get("status") if isinstance(ci, dict) else getattr(ci, "status", None)
            if status:
                statuses.append(status)

    assert statuses, "No code_interpreter_call status events seen"
    assert statuses[-1] == "completed", "code_interpreter_call did not complete"

    # Outputs captured
    assert outputs_seen, "No code interpreter outputs captured"

    # Assistant text references numeric result
    full_text = "".join(assembled_text_parts).strip()
    assert full_text, "No assistant text returned"
    assert any(token in full_text for token in ["1.414", "1.41", "1.415", "1.4142"]), "Result not mentioned"
