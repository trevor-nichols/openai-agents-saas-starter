from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_storage_presign_and_list(http_client: httpx.AsyncClient, smoke_state: SmokeState):
    headers = auth_headers(smoke_state, tenant_role="owner")

    upload = await http_client.post(
        "/api/v1/storage/objects/upload-url",
        json={
            "filename": "sample.txt",
            "mime_type": "text/plain",
            "size_bytes": 10,
        },
        headers=headers,
    )
    assert upload.status_code == 201, upload.text
    body = upload.json()
    assert body.get("upload_url")
    assert body.get("method") == "PUT"

    listing = await http_client.get("/api/v1/storage/objects", headers=headers)
    assert listing.status_code == 200
    items = listing.json().get("items", [])
    assert isinstance(items, list)
