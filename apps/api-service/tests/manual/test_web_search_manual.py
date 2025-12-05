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

import httpx
import pytest

from app.api.v1.shared.streaming import StreamingEvent, UrlCitation


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

            tool_seen = False
            citation_seen = False
            events: list[StreamingEvent] = []
            assembled_text_parts: list[str] = []

            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                try:
                    event = json.loads(line[5:].lstrip())
                except json.JSONDecodeError:
                    continue

                parsed = StreamingEvent.model_validate(event)
                events.append(parsed)

                tool_call = event.get("tool_call") or {}
                call = tool_call.get("web_search_call") if isinstance(tool_call, dict) else None
                if call and call.get("status") == "completed":
                    tool_seen = True

                for ann in event.get("annotations") or []:
                    if isinstance(ann, dict) and ann.get("type") == "url_citation":
                        citation_seen = True

                if parsed.text_delta:
                    assembled_text_parts.append(parsed.text_delta)

                if event.get("is_terminal"):
                    break

    # Structural assertions on captured events
    assert events, "Expected at least one streaming event"
    assert events[-1].is_terminal, "Stream must end with a terminal event"

    # Sequence numbers (when present) are non-decreasing
    seqs = [e.sequence_number for e in events if e.sequence_number is not None]
    assert seqs == sorted(seqs), "sequence_number should be monotonically increasing"

    # response_id stays stable across events (when present)
    resp_ids = {e.response_id for e in events if e.response_id}
    assert len(resp_ids) <= 1, "response_id changed mid-stream"

    # Web search call transitions to completed
    status_values = []
    for e in events:
        ws = None
        if isinstance(e.tool_call, dict):
            ws = e.tool_call.get("web_search_call")
        elif e.tool_call:
            ws = getattr(e.tool_call, "web_search_call", None)
        if ws:
            status = ws.get("status") if isinstance(ws, dict) else getattr(ws, "status", None)
            if status:
                status_values.append(status)

    assert status_values, f"No web_search_call status events seen; events={len(events)}"
    assert status_values[-1] == "completed", "web_search_call did not complete"

    # Citations are present and well-formed
    all_annotations = []
    for e in events:
        anns = e.annotations or []
        all_annotations.extend(anns)
    url_annotations = [a for a in all_annotations if isinstance(a, UrlCitation)]
    assert url_annotations, "Expected at least one url_citation annotation"
    assert all(a.url for a in url_annotations), "Citation missing URL"

    # Assistant text is non-empty and mentions at least one cited URL
    full_text = "".join(assembled_text_parts).strip()
    assert full_text, "No assistant text returned"
    assert any(a.url in full_text for a in url_annotations), "Response text lacks cited URLs"

    assert tool_seen, "Expected at least one web_search_call in the stream"
    assert citation_seen, "Expected at least one url_citation in the stream"
