"""Session delta projection for workflow runs."""

from __future__ import annotations

import logging
from typing import Any

from app.services.agents.event_log import EventProjector
from app.services.agents.session_items import compute_session_delta, get_session_items

logger = logging.getLogger(__name__)


class SessionDeltaProjector:
    def __init__(
        self,
        *,
        event_projector: EventProjector,
        conversation_id: str,
        tenant_id: str,
        workflow_run_id: str,
        session_handle: Any,
    ) -> None:
        self._event_projector = event_projector
        self._conversation_id = conversation_id
        self._tenant_id = tenant_id
        self._workflow_run_id = workflow_run_id
        self._session_handle = session_handle

    async def get_session_items(self) -> list[dict[str, Any]]:
        return await get_session_items(self._session_handle)

    async def ingest_delta(
        self,
        *,
        pre_items: list[dict[str, Any]],
        agent: str | None,
        model: str | None,
        response_id: str | None,
        session_items: list[dict[str, Any]] | None = None,
    ) -> None:
        post_items = session_items if session_items is not None else await self.get_session_items()
        if not post_items:
            return
        delta = session_items if session_items is not None else compute_session_delta(
            pre_items, post_items
        )
        if not delta:
            return
        try:
            await self._event_projector.ingest_session_items(
                conversation_id=self._conversation_id,
                tenant_id=self._tenant_id,
                session_items=delta,
                agent=agent,
                model=model,
                response_id=response_id,
                workflow_run_id=self._workflow_run_id,
            )
        except Exception:
            logger.exception(
                "workflow_event_projection_failed",
                extra={
                    "conversation_id": self._conversation_id,
                    "workflow_run_id": self._workflow_run_id,
                    "agent": agent,
                },
            )


__all__ = ["SessionDeltaProjector"]
