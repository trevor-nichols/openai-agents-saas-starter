"""Attachment ingestion helpers for workflow runs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import ConversationAttachment
from app.services.agents.attachment_utils import collect_container_file_citations_from_event
from app.services.agents.attachments import AttachmentService
from app.services.agents.context import ConversationActorContext
from app.services.workflows.types import WorkflowStepResult


class WorkflowAttachmentCollector:
    def __init__(
        self,
        *,
        attachment_service: AttachmentService,
        actor: ConversationActorContext,
        conversation_id: str,
    ) -> None:
        self._attachment_service = attachment_service
        self._actor = actor
        self._conversation_id = conversation_id
        self.attachments: list[ConversationAttachment] = []
        self._seen_tool_calls: set[str] = set()
        self._seen_container_files: set[str] = set()
        self._pending_container_citations: list[
            tuple[Mapping[str, Any], str | None, str | None]
        ] = []

    async def ingest_step_outputs(self, steps_results: Sequence[WorkflowStepResult]) -> None:
        ingest_container_files = self._attachment_service.ingest_container_file_citations
        for step in steps_results:
            tool_outputs = getattr(step.response, "tool_outputs", None)
            if not tool_outputs:
                continue
            images = await self._attachment_service.ingest_image_outputs(
                tool_outputs,
                actor=self._actor,
                conversation_id=self._conversation_id,
                agent_key=step.agent_key,
                response_id=step.response.response_id,
                seen_tool_calls=self._seen_tool_calls,
            )
            if images:
                self.attachments.extend(images)

            container_files = await ingest_container_files(
                tool_outputs,
                actor=self._actor,
                conversation_id=self._conversation_id,
                agent_key=step.agent_key,
                response_id=step.response.response_id,
                seen_citations=self._seen_container_files,
            )
            if container_files:
                self.attachments.extend(container_files)

    async def ingest_stream_event(self, event: AgentStreamEvent) -> None:
        new_citations = collect_container_file_citations_from_event(
            event, seen=self._seen_container_files
        )
        for ann in new_citations:
            self._pending_container_citations.append(
                (dict(ann), event.step_agent or event.agent, event.response_id)
            )

        attachment_sources: list[Mapping[str, Any]] = []
        if isinstance(event.payload, Mapping):
            attachment_sources.append(event.payload)
        if isinstance(event.tool_call, Mapping):
            attachment_sources.append(event.tool_call)
        if not attachment_sources:
            return

        agent_key = event.step_agent or event.agent
        if not agent_key:
            return

        images = await self._attachment_service.ingest_image_outputs(
            attachment_sources,
            actor=self._actor,
            conversation_id=self._conversation_id,
            agent_key=str(agent_key),
            response_id=event.response_id,
            seen_tool_calls=self._seen_tool_calls,
        )
        if not images:
            return

        self.attachments.extend(images)
        payloads: list[Mapping[str, Any]] = [
            cast(Mapping[str, Any], self._attachment_service.to_attachment_payload(att))
            for att in images
        ]
        if event.attachments is None:
            event.attachments = payloads
        else:
            event.attachments.extend(payloads)

    async def finalize_stream_container_citations(
        self,
        *,
        fallback_agent_key: str | None,
    ) -> None:
        if not self._pending_container_citations:
            return
        ingest_container_files = self._attachment_service.ingest_container_file_citations
        grouped: dict[str, list[tuple[Mapping[str, Any], str | None]]] = {}
        for citation, agent_key, response_id in self._pending_container_citations:
            grouped.setdefault(agent_key or "", []).append((citation, response_id))
        for agent_key, items in grouped.items():
            citations = [c for c, _ in items]
            response_id = next((rid for _, rid in items if rid), None)
            resolved_agent = agent_key or (fallback_agent_key or "")
            container_files = await ingest_container_files(
                citations,
                actor=self._actor,
                conversation_id=self._conversation_id,
                agent_key=resolved_agent,
                response_id=response_id,
            )
            if container_files:
                self.attachments.extend(container_files)


__all__ = ["WorkflowAttachmentCollector"]
