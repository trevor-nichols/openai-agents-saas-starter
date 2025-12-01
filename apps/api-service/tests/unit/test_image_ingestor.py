import base64
import pytest
from uuid import uuid4

from app.services.agents.image_ingestor import ingest_image_output
from app.services.storage.service import StorageService
from app.core.settings import get_settings


class StubStorage(StorageService):
    def __init__(self):
        # Bypass super init; we won't hit base members that need session_factory
        pass

    async def put_object(self, **kwargs):
        class Obj:
            def __init__(self):
                self.id = uuid4()
                self.checksum_sha256 = "abc"
                self.created_at = None

        return Obj()

    async def get_presigned_download(self, *, tenant_id, object_id):
        class Url:
            url = "https://example.com/file.png"

        class Ref:
            checksum_sha256 = "abc"
            created_at = None
        return Url(), Ref()


@pytest.mark.asyncio
async def test_ingest_image_output_happy_path(monkeypatch):
    data = base64.b64encode(b"testimagebytes").decode()
    settings = get_settings()
    storage = StubStorage()

    result = await ingest_image_output(
        image_b64=data,
        tenant_id=str(uuid4()),
        user_id=None,
        conversation_id=str(uuid4()),
        agent_key="triage",
        tool_call_id="tc_1",
        response_id="r_1",
        image_format="png",
        quality="high",
        background="auto",
        storage_service=storage, 
    )

    assert result.attachment.object_id
    assert result.attachment.filename.endswith(".png")
    assert result.size_bytes == len(b"testimagebytes")


@pytest.mark.asyncio
async def test_ingest_image_output_rejects_large(monkeypatch):
    settings = get_settings()
    big = b"0" * ((settings.image_output_max_mb + 1) * 1024 * 1024)
    data = base64.b64encode(big).decode()
    storage = StubStorage()

    with pytest.raises(ValueError):
        await ingest_image_output(
            image_b64=data,
            tenant_id=str(uuid4()),
            user_id=None,
            conversation_id=str(uuid4()),
            agent_key="triage",
            tool_call_id="tc_1",
            response_id="r_1",
            image_format="png",
            quality="high",
            background="auto",
            storage_service=storage, 
        )
