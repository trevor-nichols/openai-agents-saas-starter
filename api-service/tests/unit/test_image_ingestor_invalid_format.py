import base64
import pytest
import uuid

from app.services.agents.image_ingestor import ingest_image_output
from app.services.storage.service import StorageService


class StubStorage(StorageService):
    def __init__(self):
        pass

    async def put_object(self, **kwargs):
        class Obj:
            def __init__(self):
                self.id = uuid.uuid4()
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
async def test_ingest_rejects_bad_format():
    data = base64.b64encode(b"123").decode()
    storage = StubStorage()
    with pytest.raises(ValueError):
        await ingest_image_output(
            image_b64=data,
            tenant_id=str(uuid.uuid4()),
            user_id=None,
            conversation_id=str(uuid.uuid4()),
            agent_key="triage",
            tool_call_id="tc_1",
            response_id="r_1",
            image_format="tiff",
            quality="high",
            background="auto",
            storage_service=storage
        )
