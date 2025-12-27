from __future__ import annotations

from typing import Any

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import require_enabled
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


async def test_assets_list_detail_download_thumbnail_delete(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
    smoke_seed: dict[str, Any],
) -> None:
    require_enabled(smoke_config.enable_assets, reason="SMOKE_ENABLE_ASSETS not enabled")

    tenant_entry = smoke_seed["tenants"][smoke_config.tenant_slug]
    assets = tenant_entry.get("assets", {})
    if not assets:
        pytest.skip("No seeded assets; enable SMOKE_ENABLE_ASSETS to seed fixtures.")

    asset_entry = next(iter(assets.values()))
    asset_id = asset_entry["asset_id"]

    headers = auth_headers(smoke_state, tenant_role="owner")

    listing = await http_client.get("/api/v1/assets", headers=headers)
    assert listing.status_code == 200, listing.text
    items = listing.json().get("items", [])
    assert isinstance(items, list)
    assert any(item.get("id") == asset_id for item in items)

    detail = await http_client.get(f"/api/v1/assets/{asset_id}", headers=headers)
    assert detail.status_code == 200, detail.text
    detail_body = detail.json()
    assert detail_body.get("id") == asset_id

    download = await http_client.get(f"/api/v1/assets/{asset_id}/download-url", headers=headers)
    assert download.status_code == 200, download.text
    download_body = download.json()
    assert download_body.get("asset_id") == asset_id
    assert download_body.get("download_url")
    assert download_body.get("method") == "GET"

    thumbs = await http_client.post(
        "/api/v1/assets/thumbnail-urls",
        json={"asset_ids": [asset_id]},
        headers=headers,
    )
    assert thumbs.status_code == 200, thumbs.text
    thumb_body = thumbs.json()
    thumb_items = thumb_body.get("items", [])
    assert any(item.get("asset_id") == asset_id for item in thumb_items)

    delete = await http_client.delete(f"/api/v1/assets/{asset_id}", headers=headers)
    assert delete.status_code == 204
