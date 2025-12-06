"""Read-only conversation queries kept separate from chat orchestration."""

from __future__ import annotations

from typing import Any, Literal

from app.bootstrap.container import wire_storage_service
from app.domain.conversations import ConversationRepository
from app.services.agents.attachments import AttachmentService
from app.services.agents.context import ConversationActorContext
from app.services.agents.history import ConversationHistoryService
from app.services.conversation_service import ConversationService, SearchResult


class ConversationQueryService:
    """Facilitates history, search, and event reads for conversations."""

    def __init__(
        self,
        *,
        conversation_service: ConversationService,
        history_service: ConversationHistoryService,
    ) -> None:
        self._conversation_service = conversation_service
        self._history_service = history_service

    async def get_history(
        self, conversation_id: str, *, actor: ConversationActorContext
    ) -> Any:
        return await self._history_service.get_history(conversation_id, actor=actor)

    async def get_events(
        self,
        conversation_id: str,
        *,
        actor: ConversationActorContext,
        workflow_run_id: str | None = None,
    ) -> list[Any]:
        return await self._conversation_service.get_run_events(
            conversation_id,
            tenant_id=actor.tenant_id,
            workflow_run_id=workflow_run_id,
        )

    async def list_summaries(
        self,
        *,
        actor: ConversationActorContext,
        limit: int = 50,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
        updated_after: Any | None = None,
    ) -> tuple[list[Any], str | None]:
        return await self._history_service.list_summaries(
            actor=actor,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent_entrypoint,
            updated_after=updated_after,
        )

    async def search(
        self,
        *,
        actor: ConversationActorContext,
        query: str,
        limit: int = 20,
        cursor: str | None = None,
        agent_entrypoint: str | None = None,
    ) -> tuple[list[SearchResult], str | None]:
        return await self._history_service.search(
            actor=actor,
            query=query,
            limit=limit,
            cursor=cursor,
            agent_entrypoint=agent_entrypoint,
        )

    async def clear(self, conversation_id: str, *, actor: ConversationActorContext) -> None:
        await self._history_service.clear(conversation_id, actor=actor)

    async def get_messages_page(
        self,
        conversation_id: str,
        *,
        actor: ConversationActorContext,
        limit: int,
        cursor: str | None,
        direction: Literal["asc", "desc"],
    ) -> tuple[list[Any], str | None]:
        return await self._history_service.get_messages_page(
            conversation_id,
            actor=actor,
            limit=limit,
            cursor=cursor,
            direction=direction,
        )

    @property
    def repository(self) -> ConversationRepository:
        return self._conversation_service.repository


def build_conversation_query_service(
    *,
    conversation_service: ConversationService,
    history_service: ConversationHistoryService,
) -> ConversationQueryService:
    return ConversationQueryService(
        conversation_service=conversation_service,
        history_service=history_service,
    )


def get_conversation_query_service() -> ConversationQueryService:
    from app.bootstrap.container import get_container

    container = get_container()
    if getattr(container, "conversation_query_service", None) is None:
        if container.storage_service is None:
            wire_storage_service(container)
        storage_service = container.storage_service
        if storage_service is None:  # pragma: no cover - defensive
            raise RuntimeError("Storage service is not configured")
        container.conversation_query_service = build_conversation_query_service(
            conversation_service=container.conversation_service,
            history_service=ConversationHistoryService(
                container.conversation_service,
                AttachmentService(lambda: storage_service),
            ),
        )
    svc = container.conversation_query_service
    if svc is None:  # pragma: no cover - defensive
        raise RuntimeError("ConversationQueryService not initialized")
    return svc


__all__ = [
    "ConversationQueryService",
    "build_conversation_query_service",
    "get_conversation_query_service",
]
