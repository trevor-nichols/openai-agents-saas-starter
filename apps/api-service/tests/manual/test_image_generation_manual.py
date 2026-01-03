"""Manual streaming check for the hosted image_generation tool.

Run locally only (opt-in):

    pytest tests/manual/test_image_generation_manual.py -m manual --run-manual --asyncio-mode=auto

Assertions:
- HTTP 200
- Stream events validate against StreamingEvent and end with terminal
- image_generation_call status reaches completed
- At least one attachment is stored/presigned
- Assistant returns non-empty text description

If an assertion fails, the raw SSE lines are written to a temp file to inspect
the exact payload (handy when schema drift occurs).
"""

from __future__ import annotations

import json
import os
import tempfile
from getpass import getpass
from pathlib import Path

import httpx
import pytest

from app.api.v1.shared.streaming import ChunkDeltaEvent, PublicSseEvent, PublicSseEventBase
from tests.utils.stream_assertions import (
    assert_image_generation_expectations,
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
async def test_image_generation_streaming_manual() -> None:
    base_url = _default_base_url()
    # Image gen can be slower; default to 3 minutes unless overridden.
    timeout = float(os.getenv("MANUAL_TIMEOUT", "180"))

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
            "Generate a simple line-drawn stick figure, standing upright. "
            "Use the image generation tool, include a brief textual description, and keep text concise."
        ),
        "share_location": False,
    }

    raw_lines: list[str] = []
    events: list[PublicSseEventBase] = []

    url = f"{base_url.rstrip('/')}/api/v1/chat/stream"
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            body = (await resp.aread()).decode("utf-8", "ignore")
            assert resp.status_code == 200, f"status {resp.status_code}: {body}"

            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                raw_lines.append(line)
                try:
                    event = json.loads(line[5:].lstrip())
                except json.JSONDecodeError:
                    continue

                parsed = PublicSseEvent.model_validate(event).root
                events.append(parsed)

                if getattr(parsed, "kind", None) in {"final", "error"}:
                    break

    try:
        assert_image_generation_expectations(events, require_partial_chunks=False)
    except AssertionError as exc:  # pragma: no cover - debugging aid for manual runs
        dump_dir = Path(tempfile.mkdtemp(prefix="image_gen_stream_"))
        dump_path = dump_dir / "stream.ndjson"
        dump_path.write_text("\n".join(raw_lines), encoding="utf-8")
        pytest.fail(f"{exc}\nRaw stream saved to {dump_path}")

    repo_root = Path(__file__).resolve().parents[4]
    default_path = (
        repo_root
        / "docs"
        / "contracts"
        / "public-sse-streaming"
        / "examples"
        / "chat-image-generation-partials.ndjson"
    )
    if os.getenv("MANUAL_RECORD_STREAM_TO") == "":
        has_partials = any(
            isinstance(e, ChunkDeltaEvent) and e.target.field == "partial_image_b64" for e in events
        )
        if not has_partials:
            pytest.skip(
                "No partial_image_b64 chunk events emitted; refusing to overwrite the canonical"
                " chat-image-generation-partials.ndjson fixture. Re-run until partials appear,"
                " or set MANUAL_RECORD_STREAM_TO to a different path."
            )
    maybe_record_stream(events, env_var="MANUAL_RECORD_STREAM_TO", default_path=default_path)
