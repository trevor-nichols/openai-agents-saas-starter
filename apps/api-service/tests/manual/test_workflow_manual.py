"""Manual streaming check for workflow run-stream (analysis_code).

Run locally only, opt-in:

    pytest tests/manual/test_workflow_manual.py -m manual --run-manual --asyncio-mode=auto

Auth strategy:
- If MANUAL_ACCESS_TOKEN and MANUAL_TENANT_ID are set, use them.
- Otherwise prompt once for the dev user's password (default email dev@example.com) and log in.

Base URL:
- Use API_BASE_URL if set; else http://localhost:{PORT or 8000}.

This test is skipped in CI by default via the `manual` marker and --run-manual flag.
"""

from __future__ import annotations

import json
import os
from getpass import getpass
from pathlib import Path

import httpx
import pytest

from app.api.v1.shared.streaming import PublicSseEvent, PublicSseEventBase
from tests.utils.stream_assertions import (
    assembled_text,
    assert_common_stream,
    maybe_record_stream,
)


def _default_base_url() -> str:
    api_env = os.getenv("API_BASE_URL")
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
async def test_analysis_code_workflow_stream_manual() -> None:
    base_url = _default_base_url()
    timeout = float(os.getenv("MANUAL_TIMEOUT", "90"))

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
        "message": os.getenv(
            "MANUAL_MESSAGE",
            "Find one uplifting headline from today using web search, then have the code "
            "assistant turn it into a two-bullet summary. Include the cited URL.",
        ),
        "share_location": True,
    }

    url = f"{base_url.rstrip('/')}/api/v1/workflows/analysis_code/run-stream"
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            if resp.status_code != 200:
                body = (await resp.aread()).decode("utf-8", "ignore")
                assert False, f"status {resp.status_code}: {body}"

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

    assert_common_stream(events)
    assert events[-1].workflow is not None
    assert events[-1].workflow.workflow_key == "analysis_code"
    steps_seen = {e.workflow.step_name for e in events if e.workflow and e.workflow.step_name}
    assert "analysis" in steps_seen, f"Analysis step missing; saw {steps_seen}"
    # Code step may be skipped if the first agent fully answers; log when absent.
    if "code" not in steps_seen:
        pytest.skip(f"Code step not invoked in this run (steps seen: {steps_seen})")
    assert assembled_text(events), "No assistant text returned"

    repo_root = Path(__file__).resolve().parents[4]
    default_path = (
        repo_root
        / "docs"
        / "contracts"
        / "public-sse-streaming"
        / "examples"
        / "workflow-analysis-code.ndjson"
    )
    maybe_record_stream(events, env_var="MANUAL_RECORD_STREAM_TO", default_path=default_path)
