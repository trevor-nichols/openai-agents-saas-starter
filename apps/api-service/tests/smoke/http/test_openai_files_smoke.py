from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import require_enabled
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_openai_file_download_proxy(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    require_enabled(smoke_config.enable_openai_files, reason="SMOKE_ENABLE_OPENAI_FILES not enabled")
    if not smoke_config.openai_file_id:
        pytest.skip("SMOKE_OPENAI_FILE_ID not set; provide a valid OpenAI file id.")

    resp = await http_client.get(
        f"/api/v1/openai/files/{smoke_config.openai_file_id}/download",
        headers=auth_headers(smoke_state, tenant_role="owner"),
    )
    assert resp.status_code == 200, resp.text
    content_type = resp.headers.get("content-type", "")
    assert "application/octet-stream" in content_type
    assert "content-disposition" in {key.lower() for key in resp.headers}
