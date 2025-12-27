from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_agent_input_upload(http_client: httpx.AsyncClient, smoke_state: SmokeState) -> None:
    headers = auth_headers(smoke_state, tenant_role="owner")
    payload = {
        "filename": "agent-input.txt",
        "mime_type": "text/plain",
        "size_bytes": 12,
        "metadata": {"fixture": "smoke"},
    }
    if smoke_state.conversation_id:
        payload["conversation_id"] = smoke_state.conversation_id

    resp = await http_client.post("/api/v1/uploads/agent-input", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body.get("object_id")
    assert body.get("upload_url")
    assert body.get("method") == "PUT"
