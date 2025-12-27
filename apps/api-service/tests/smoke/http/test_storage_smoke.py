from __future__ import annotations

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_storage_presign_list_download_delete(
    http_client: httpx.AsyncClient, smoke_state: SmokeState
):
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
    object_id = body.get("object_id")
    assert object_id
    assert body.get("upload_url")
    assert body.get("method") == "PUT"

    listing = await http_client.get("/api/v1/storage/objects", headers=headers)
    assert listing.status_code == 200
    items = listing.json().get("items", [])
    assert isinstance(items, list)

    download = await http_client.get(
        f"/api/v1/storage/objects/{object_id}/download-url", headers=headers
    )
    assert download.status_code == 200, download.text
    download_body = download.json()
    assert download_body.get("object_id") == object_id
    assert download_body.get("download_url")
    assert download_body.get("method") == "GET"

    delete = await http_client.delete(f"/api/v1/storage/objects/{object_id}", headers=headers)
    assert delete.status_code == 204

    delete_again = await http_client.delete(
        f"/api/v1/storage/objects/{object_id}", headers=headers
    )
    assert delete_again.status_code == 204
