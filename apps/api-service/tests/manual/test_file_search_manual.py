"""Manual streaming check for the hosted file_search tool.

Run locally only, opt-in:

    pytest tests/manual/test_file_search_manual.py -m manual --run-manual --asyncio-mode=auto

Prereqs:
- A vector store with at least one completed file attachment for the tenant.
- Either set MANUAL_ACCESS_TOKEN and MANUAL_TENANT_ID or use the dev user credentials.

Assertions:
- HTTP 200
- SSE events conform to StreamingEvent; terminal event present
- file_search_call status reaches completed
- At least one file_citation emitted for the selected store/file
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx
import pytest

from app.api.v1.shared.streaming import PublicSseEvent, PublicSseEventBase
from tests.utils.stream_assertions import (
    assert_file_search_expectations,
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


async def _pick_vector_store_with_file(
    base_url: str, headers: dict[str, str], timeout: float
) -> tuple[str, str]:
    """Return (store_openai_id, file_openai_id) or skip if none ready."""

    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        stores_resp = await client.get(f"{base_url.rstrip('/')}/api/v1/vector-stores?limit=50")
        if stores_resp.status_code != 200:
            pytest.skip(f"List vector stores failed: {stores_resp.status_code} {stores_resp.text}")
        stores = stores_resp.json().get("items", [])
        if not stores:
            pytest.skip("No vector stores found; create one and attach a file before running this test.")

        for store in stores:
            store_id = store.get("id")
            openai_id = store.get("openai_id")
            files_resp = await client.get(
                f"{base_url.rstrip('/')}/api/v1/vector-stores/{store_id}/files?status=completed&limit=50"
            )
            if files_resp.status_code != 200:
                continue
            files = files_resp.json().get("items", [])
            if not files:
                continue
            # pick the first completed file
            file = files[0]
            file_id = file.get("openai_file_id")
            if openai_id and file_id:
                return str(openai_id), str(file_id)

    pytest.skip(
        "No vector store files in 'completed' status; attach a file to a store before running this test."
    )


async def _ensure_primary_store(
    base_url: str, headers: dict[str, str], timeout: float
) -> tuple[str, str]:
    """Ensure a primary vector store exists; return (store_uuid, openai_id)."""

    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        resp = await client.get(f"{base_url.rstrip('/')}/api/v1/vector-stores?limit=50")
        if resp.status_code != 200:
            pytest.skip(f"List vector stores failed: {resp.status_code} {resp.text}")
        stores = resp.json().get("items", [])
        for store in stores:
            if store.get("name") == "primary" and store.get("openai_id"):
                return str(store["id"]), str(store["openai_id"])

        create = await client.post(
            f"{base_url.rstrip('/')}/api/v1/vector-stores",
            json={"name": "primary", "description": "Primary store for manual tests"},
        )
        if create.status_code not in (200, 201):
            pytest.skip(f"Create vector store failed: {create.status_code} {create.text}")
        body = create.json()
        return str(body["id"]), str(body["openai_id"])


async def _upload_file_to_openai(local_path: Path, timeout: float) -> str:
    """Upload a local file to OpenAI Files API; return file_id."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY is required to upload FILE_SEARCH_LOCAL_FILE")

    async with httpx.AsyncClient(timeout=timeout) as client:
        with local_path.open("rb") as fh:
            files: list[tuple[str, tuple[str | None, Any, str | None]]] = [
                ("file", (local_path.name, fh, "application/octet-stream")),
                ("purpose", (None, "assistants", None)),
            ]
            resp = await client.post(
                "https://api.openai.com/v1/files",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
            )
        if resp.status_code != 200:
            pytest.skip(f"OpenAI file upload failed: {resp.status_code} {resp.text}")
        return resp.json()["id"]


async def _attach_file_to_store(
    base_url: str,
    headers: dict[str, str],
    timeout: float,
    store_id: str,
    openai_file_id: str,
) -> str:
    """Attach an OpenAI file to the given store; return file_openai_id."""

    attach_url = f"{base_url.rstrip('/')}/api/v1/vector-stores/{store_id}/files"
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        resp = await client.post(
            attach_url,
            json={"file_id": openai_file_id, "poll": True},
        )
        if resp.status_code not in (200, 201, 409):
            pytest.skip(f"Attach file failed: {resp.status_code} {resp.text}")

        # 409 means already attached; that's fine
        if resp.status_code in (200, 201):
            data = resp.json()
            status = data.get("status")
            # If still indexing, poll a few times for completion
            file_uuid = data.get("id")
            if status != "completed" and file_uuid:
                detail_url = f"{attach_url}/{file_uuid}"
                for _ in range(5):
                    await asyncio.sleep(2)
                    check = await client.get(detail_url)
                    if check.status_code != 200:
                        break
                    status = check.json().get("status")
                    if status == "completed":
                        break

        return openai_file_id


@pytest.mark.manual
@pytest.mark.asyncio
async def test_file_search_streaming_manual() -> None:
    base_url = _default_base_url()
    timeout = float(os.getenv("MANUAL_TIMEOUT", "60"))

    # Default to the bundled sample PDF; allow override via env if desired.
    default_file = Path(__file__).resolve().parent.parent / "utils" / "test.pdf"
    local_file = os.getenv("FILE_SEARCH_LOCAL_FILE")
    if not local_file:
        local_file = str(default_file)

    token = os.getenv("MANUAL_ACCESS_TOKEN")
    tenant_id = os.getenv("MANUAL_TENANT_ID")
    if not token or not tenant_id:
        email = os.getenv("DEV_USER_EMAIL", "dev@example.com")
        password = os.getenv("DEV_USER_PASSWORD")
        if not password:
            pytest.skip("Set DEV_USER_PASSWORD or MANUAL_ACCESS_TOKEN/MANUAL_TENANT_ID for manual tests")
        token, tenant_id = await _login_dev_user(base_url, timeout, email=email, password=password)

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": tenant_id,
        "X-Tenant-Role": "owner",
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }

    store_openai_id: str
    file_openai_id: str

    if local_file:
        path = Path(local_file).expanduser().resolve()
        if not path.exists():
            pytest.skip(f"FILE_SEARCH_LOCAL_FILE not found: {path}")
        store_uuid, store_openai_id = await _ensure_primary_store(base_url, headers, timeout)
        uploaded_file_id = await _upload_file_to_openai(path, timeout)
        file_openai_id = await _attach_file_to_store(
            base_url, headers, timeout, store_uuid, uploaded_file_id
        )
    else:
        store_openai_id, file_openai_id = await _pick_vector_store_with_file(
            base_url, headers, timeout
        )

    payload: dict[str, Any] = {
        "agent_type": "researcher",
        "message": (
            "Use the file_search tool on the provided vector store to answer: "
            "Summarize the attached file in one sentence and cite it."
        ),
        "share_location": False,
        # Ensure the request targets the selected store
        "context": {"vector_store_id": store_openai_id},
    }

    url = f"{base_url.rstrip('/')}/api/v1/chat/stream"
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            body = (await resp.aread()).decode("utf-8", "ignore")
            assert resp.status_code == 200, f"status {resp.status_code}: {body}"

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

    assert_file_search_expectations(events, expected_store_id=store_openai_id)

    repo_root = Path(__file__).resolve().parents[4]
    default_path = (
        repo_root
        / "docs"
        / "contracts"
        / "public-sse-streaming"
        / "examples"
        / "chat-file-search.ndjson"
    )
    maybe_record_stream(events, env_var="MANUAL_RECORD_STREAM_TO", default_path=default_path)
