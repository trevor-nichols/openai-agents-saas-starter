from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import require_enabled
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_sessions_and_logout(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    require_enabled(smoke_config.enable_auth_extended, reason="SMOKE_ENABLE_AUTH_EXTENDED not enabled")

    headers = auth_headers(smoke_state)

    sessions_resp = await http_client.get("/api/v1/auth/sessions", headers=headers)
    assert sessions_resp.status_code == 200, sessions_resp.text
    session_body = sessions_resp.json()
    sessions = session_body.get("sessions", [])
    assert isinstance(sessions, list)
    assert sessions

    session_id = sessions[0].get("id")
    assert session_id

    revoke_resp = await http_client.delete(
        f"/api/v1/auth/sessions/{session_id}",
        headers=headers,
    )
    assert revoke_resp.status_code in {200, 404}, revoke_resp.text

    logout_resp = await http_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": smoke_state.refresh_token},
        headers=headers,
    )
    assert logout_resp.status_code == 200, logout_resp.text
    logout_body = logout_resp.json()
    assert isinstance(logout_body.get("data", {}).get("revoked"), bool)

    logout_all = await http_client.post("/api/v1/auth/logout/all", headers=headers)
    assert logout_all.status_code == 200, logout_all.text
    logout_all_body = logout_all.json()
    revoked_count = logout_all_body.get("data", {}).get("revoked")
    assert isinstance(revoked_count, int)
