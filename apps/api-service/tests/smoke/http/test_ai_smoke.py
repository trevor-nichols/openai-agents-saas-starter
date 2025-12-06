from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_chat_and_workflow_run(
    http_client: httpx.AsyncClient, smoke_config: SmokeConfig, smoke_state: SmokeState
) -> None:
    if not smoke_config.enable_ai:
        pytest.skip("SMOKE_ENABLE_AI not enabled")

    headers = auth_headers(smoke_state)

    chat = await http_client.post(
        "/api/v1/chat",
        json={"message": "Hello", "agent_type": "triage"},
        headers=headers,
    )
    assert chat.status_code == 200, chat.text
    chat_body = chat.json()
    assert chat_body.get("conversation_id")

    workflow = await http_client.post(
        "/api/v1/workflows/analysis_code/run",
        json={"message": "Summarize"},
        headers=headers,
    )
    assert workflow.status_code == 200, workflow.text
    wf_body = workflow.json()
    assert wf_body.get("workflow_key") == "analysis_code"
    assert wf_body.get("workflow_run_id")
