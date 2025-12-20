"""Best-effort linking of assets to conversation messages."""

from __future__ import annotations

import logging
import uuid

from app.domain.conversations import ConversationAttachment
from app.services.assets.service import AssetService

logger = logging.getLogger(__name__)


class AssetLinker:
    """Link storage-backed assets to persisted messages when possible."""

    def __init__(self, asset_service: AssetService | None) -> None:
        self._asset_service = asset_service

    async def maybe_link_assets(
        self,
        *,
        tenant_id: str,
        message_id: int | None,
        attachments: list[ConversationAttachment],
    ) -> None:
        if self._asset_service is None or message_id is None or not attachments:
            return
        try:
            storage_object_ids = [uuid.UUID(att.object_id) for att in attachments]
        except Exception:
            logger.warning(
                "asset.link_failed_invalid_object_ids",
                extra={"tenant_id": tenant_id, "message_id": message_id},
            )
            return
        try:
            await self._asset_service.link_assets_to_message(
                tenant_id=uuid.UUID(tenant_id),
                message_id=message_id,
                storage_object_ids=storage_object_ids,
            )
        except Exception as exc:
            logger.warning(
                "asset.link_failed",
                extra={"tenant_id": tenant_id, "message_id": message_id},
                exc_info=exc,
            )
