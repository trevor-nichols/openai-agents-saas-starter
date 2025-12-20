"""Output helpers for workflow runs."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Sequence
from typing import Any

from app.domain.ai.models import AgentRunUsage
from app.domain.conversations import (
    ConversationAttachment,
    ConversationMessage,
    ConversationMetadata,
)
from app.services.agents.context import ConversationActorContext
from app.services.assets.service import AssetService
from app.services.conversation_service import ConversationService
from app.workflows._shared.specs import WorkflowSpec

logger = logging.getLogger(__name__)


def aggregate_usage(usages: Sequence[AgentRunUsage | None]) -> AgentRunUsage | None:
    totals: dict[str, int] = {}
    saw_any = False
    for usage in usages:
        if usage is None:
            continue
        for field_name in (
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "cached_input_tokens",
            "reasoning_output_tokens",
            "requests",
        ):
            value = getattr(usage, field_name, None)
            if isinstance(value, int):
                totals[field_name] = totals.get(field_name, 0) + value
                saw_any = True
    if not saw_any:
        return None
    return AgentRunUsage(
        input_tokens=totals.get("input_tokens"),
        output_tokens=totals.get("output_tokens"),
        total_tokens=totals.get("total_tokens"),
        cached_input_tokens=totals.get("cached_input_tokens"),
        reasoning_output_tokens=totals.get("reasoning_output_tokens"),
        requests=totals.get("requests"),
    )


def render_workflow_output_text(value: Any) -> str:
    """Best-effort conversion of a workflow output into message text."""

    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:  # pragma: no cover - defensive
        return str(value)


def format_stream_output(value: Any) -> tuple[str | None, Any | None]:
    if value is None:
        return None, None
    if isinstance(value, str):
        return value, None
    try:
        return json.dumps(value, ensure_ascii=False), value
    except Exception:  # pragma: no cover - defensive
        return str(value), value


class WorkflowAssistantMessageWriter:
    def __init__(
        self,
        *,
        conversation_service: ConversationService,
        asset_service: AssetService | None = None,
    ) -> None:
        self._conversation_service = conversation_service
        self._asset_service = asset_service

    async def write(
        self,
        *,
        workflow: WorkflowSpec,
        actor: ConversationActorContext,
        provider_name: str | None,
        conversation_id: str,
        response_text: str,
        attachments: list[ConversationAttachment],
        active_agent: str | None,
    ) -> None:
        message_id = await self._conversation_service.append_message(
            conversation_id,
            ConversationMessage(role="assistant", content=response_text, attachments=attachments),
            tenant_id=actor.tenant_id,
            metadata=ConversationMetadata(
                tenant_id=actor.tenant_id,
                agent_entrypoint=workflow.key,
                active_agent=active_agent,
                provider=provider_name,
                user_id=actor.user_id,
            ),
        )
        if self._asset_service and message_id is not None and attachments:
            try:
                storage_ids = [uuid.UUID(att.object_id) for att in attachments]
            except Exception:
                logger.warning(
                    "asset.link_failed_invalid_object_ids",
                    extra={
                        "tenant_id": actor.tenant_id,
                        "conversation_id": conversation_id,
                        "message_id": message_id,
                    },
                )
                return
            try:
                await self._asset_service.link_assets_to_message(
                    tenant_id=uuid.UUID(actor.tenant_id),
                    message_id=message_id,
                    storage_object_ids=storage_ids,
                )
            except Exception as exc:
                logger.warning(
                    "asset.link_failed",
                    extra={
                        "tenant_id": actor.tenant_id,
                        "conversation_id": conversation_id,
                        "message_id": message_id,
                    },
                    exc_info=exc,
                )


__all__ = [
    "WorkflowAssistantMessageWriter",
    "aggregate_usage",
    "format_stream_output",
    "render_workflow_output_text",
]
