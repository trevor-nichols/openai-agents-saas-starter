"""Streaming orchestration helpers for AgentService.

This module keeps `AgentService.chat_stream` focused on wiring and persistence by
extracting the event-by-event streaming normalization and guardrail forwarding.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from app.domain.ai.lifecycle import LifecycleEventSink
from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import ConversationAttachment
from app.services.agents.attachment_utils import collect_container_file_citations_from_event
from app.services.agents.attachments import AttachmentService
from app.services.agents.context import ConversationActorContext

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class StreamOutcome:
    complete_response: str = ""
    attachments: list[ConversationAttachment] = field(default_factory=list)
    current_agent: str = ""
    current_output_schema: Mapping[str, Any] | None = None
    handoff_count: int = 0
    last_response_id: str | None = None


class AgentStreamProcessor:
    """Normalizes stream events and accumulates final run state."""

    def __init__(
        self,
        *,
        lifecycle_bus: LifecycleEventSink,
        provider: Any,
        actor: ConversationActorContext,
        conversation_id: str,
        entrypoint_agent: str,
        entrypoint_output_schema: Mapping[str, Any] | None,
        attachment_service: AttachmentService,
    ) -> None:
        self._bus = lifecycle_bus
        self._provider = provider
        self._actor = actor
        self._conversation_id = conversation_id
        self._entrypoint_agent = entrypoint_agent
        self._attachments = attachment_service

        self.outcome = StreamOutcome(
            current_agent=entrypoint_agent,
            current_output_schema=entrypoint_output_schema,
        )
        self._seen_tool_calls: set[str] = set()
        self._pending_container_file_citations: list[Mapping[str, Any]] = []
        self._seen_container_files: set[str] = set()

    @property
    def pending_container_file_citations(self) -> list[Mapping[str, Any]]:
        return list(self._pending_container_file_citations)

    async def iter_events(self, stream_handle: Any) -> AsyncIterator[AgentStreamEvent]:
        async for event in stream_handle.events():
            processed = await self._process_event(event)
            is_terminal = processed.is_terminal and processed.scope is None
            if is_terminal:
                if processed.response_text is None:
                    text = self.outcome.complete_response.strip()
                    processed.response_text = text or None
                if processed.usage is None and hasattr(stream_handle, "usage"):
                    processed.usage = getattr(stream_handle, "usage", None)
            yield processed
            if is_terminal:
                break

        async for leftover in self._bus.drain():
            leftover.conversation_id = self._conversation_id
            if (
                leftover.output_schema is None
                and self.outcome.current_output_schema is not None
            ):
                leftover.output_schema = self.outcome.current_output_schema
            yield leftover

        if hasattr(stream_handle, "last_response_id"):
            self.outcome.last_response_id = self.outcome.last_response_id or getattr(
                stream_handle, "last_response_id", None
            )

    async def _process_event(self, event: AgentStreamEvent) -> AgentStreamEvent:
        event.conversation_id = self._conversation_id
        is_scoped = event.scope is not None

        if not is_scoped:
            if event.kind == "agent_updated_stream_event" and event.new_agent:
                self.outcome.current_agent = event.new_agent
                descriptor = self._provider.get_agent(self.outcome.current_agent)
                if descriptor:
                    self.outcome.current_output_schema = descriptor.output_schema
                self.outcome.handoff_count += 1
                event.agent = event.new_agent

        if event.agent is None and not is_scoped:
            event.agent = self.outcome.current_agent or self._entrypoint_agent

        if event.response_id and not is_scoped:
            self.outcome.last_response_id = event.response_id

        if not is_scoped:
            if event.text_delta:
                self.outcome.complete_response += event.text_delta
            elif event.response_text and not self.outcome.complete_response:
                self.outcome.complete_response = event.response_text

        if not is_scoped:
            self._collect_container_file_citations(event)

        if not is_scoped:
            attachment_sources: list[Mapping[str, Any]] = []
            if event.payload and isinstance(event.payload, Mapping):
                attachment_sources.append(event.payload)
            if isinstance(event.tool_call, Mapping):
                attachment_sources.append(event.tool_call)

            new_attachments = await self._attachments.ingest_image_outputs(
                attachment_sources or None,
                actor=self._actor,
                conversation_id=self._conversation_id,
                agent_key=self._entrypoint_agent,
                response_id=event.response_id,
                seen_tool_calls=self._seen_tool_calls,
            )
            if new_attachments:
                self.outcome.attachments.extend(new_attachments)
                event.attachments = [
                    self._attachments.to_attachment_payload(att) for att in new_attachments
                ]

                payload: dict[str, Any] | None = None
                if event.payload is None:
                    payload = {}
                elif isinstance(event.payload, dict):
                    payload = event.payload
                elif isinstance(event.payload, Mapping):
                    payload = dict(event.payload)

                if payload is not None:
                    payload.setdefault("_attachment_note", "stored")
                    event.payload = payload

        event.payload = AgentStreamEvent._strip_unserializable(event.payload)
        event.structured_output = AgentStreamEvent._strip_unserializable(event.structured_output)
        event.response_text = None if event.response_text is None else str(event.response_text)
        if (
            not is_scoped
            and event.output_schema is None
            and self.outcome.current_output_schema is not None
        ):
            event.output_schema = self.outcome.current_output_schema

        if not is_scoped and event.is_terminal and self.outcome.current_agent:
            event.agent = self.outcome.current_agent
        if is_scoped:
            event.agent = None

        return event

    def _collect_container_file_citations(self, event: AgentStreamEvent) -> None:
        new = collect_container_file_citations_from_event(event, seen=self._seen_container_files)
        self._pending_container_file_citations.extend(new)


class GuardrailStreamForwarder:
    """Converts guardrail emissions into AgentStreamEvent and forwards to the bus."""

    def __init__(
        self,
        *,
        lifecycle_bus: LifecycleEventSink,
        conversation_id: str,
        default_agent: str,
        get_current_agent: Callable[[], str | None],
        get_last_response_id: Callable[[], str | None],
        get_fallback_response_id: Callable[[], str | None],
    ) -> None:
        self._bus = lifecycle_bus
        self._conversation_id = conversation_id
        self._default_agent = default_agent
        self._get_current_agent = get_current_agent
        self._get_last_response_id = get_last_response_id
        self._get_fallback_response_id = get_fallback_response_id

    def __call__(self, payload: Mapping[str, Any]) -> None:
        response_id = (
            payload.get("response_id")
            or self._get_last_response_id()
            or self._get_fallback_response_id()
        )
        agent_for_event = (
            payload.get("agent") or self._get_current_agent() or self._default_agent
        )

        event = AgentStreamEvent(
            kind="guardrail_result",
            conversation_id=self._conversation_id,
            agent=agent_for_event,
            response_id=response_id,
            guardrail_stage=payload.get("guardrail_stage"),
            guardrail_key=payload.get("guardrail_key"),
            guardrail_name=payload.get("guardrail_name"),
            guardrail_tripwire_triggered=payload.get("guardrail_tripwire_triggered"),
            guardrail_suppressed=payload.get("guardrail_suppressed"),
            guardrail_flagged=payload.get("guardrail_flagged"),
            guardrail_confidence=payload.get("guardrail_confidence"),
            guardrail_masked_content=payload.get("guardrail_masked_content"),
            guardrail_token_usage=payload.get("guardrail_token_usage"),
            guardrail_details=payload.get("guardrail_details"),
            tool_name=payload.get("tool_name"),
            tool_call_id=payload.get("tool_call_id"),
            payload=(
                payload.get("payload") if isinstance(payload.get("payload"), Mapping) else None
            ),
        )

        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(self._bus.emit(event))
            task.add_done_callback(lambda _: None)
        except Exception:
            logger.exception(
                "guardrail_event.emit_failed",
                extra={"stage": payload.get("guardrail_stage")},
            )


def build_guardrail_summary(events: list[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(events)
    triggered = sum(1 for ev in events if ev.get("guardrail_tripwire_triggered"))
    suppressed = sum(
        1
        for ev in events
        if ev.get("guardrail_tripwire_triggered") and ev.get("guardrail_suppressed")
    )

    by_stage: dict[str, dict[str, int]] = {}
    by_key: dict[str, int] = {}
    usage_totals: dict[str, int] = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    usage_found = False

    for ev in events:
        stage = ev.get("guardrail_stage") or "unknown"
        stage_bucket = by_stage.setdefault(stage, {"total": 0, "triggered": 0})
        stage_bucket["total"] += 1
        if ev.get("guardrail_tripwire_triggered"):
            stage_bucket["triggered"] += 1

        key = ev.get("guardrail_key")
        if key:
            by_key[key] = by_key.get(key, 0) + 1

        token_usage = ev.get("guardrail_token_usage")
        if isinstance(token_usage, dict):
            seen_usage = False
            for field_name in ("prompt_tokens", "completion_tokens", "total_tokens"):
                value = token_usage.get(field_name)
                if isinstance(value, int):
                    usage_totals[field_name] = usage_totals.get(field_name, 0) + value
                    seen_usage = True
            if seen_usage:
                usage_found = True

    summary: dict[str, Any] = {
        "total": total,
        "triggered": triggered,
        "suppressed": suppressed,
        "by_stage": by_stage,
        "by_key": by_key,
    }
    if usage_found:
        summary["token_usage"] = usage_totals

    return summary


__all__ = [
    "AgentStreamProcessor",
    "GuardrailStreamForwarder",
    "StreamOutcome",
    "build_guardrail_summary",
]
