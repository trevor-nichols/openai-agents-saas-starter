from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import fetch_sse_event_json, require_enabled
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_chat_stream_handshake(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    require_enabled(smoke_config.enable_ai, reason="SMOKE_ENABLE_AI not enabled")

    payload = {
        "message": "Hello",
        "agent_type": "triage",
    }
    event = await fetch_sse_event_json(
        http_client,
        "POST",
        "/api/v1/chat/stream",
        json=payload,
        headers=auth_headers(smoke_state),
        timeout_seconds=smoke_config.request_timeout,
    )

    assert event.get("schema") == "public_sse_v1"
    conversation_id = event.get("conversation_id")
    assert isinstance(conversation_id, str) and conversation_id
