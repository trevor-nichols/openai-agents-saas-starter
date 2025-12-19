from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from app.domain.ai.models import AgentStreamEvent

from ..streaming import (
    PUBLIC_SSE_SCHEMA_VERSION,
    ErrorEvent,
    ErrorPayload,
    FinalEvent,
    FinalPayload,
    PublicSseEventBase,
)
from .agent_updates import project_event as project_agent_update_event
from .builders import EventBuilder
from .raw import apply_attachments, terminal_final_status
from .raw import project_event as project_raw_event
from .run_items import project_event as project_run_item_event
from .state import ProjectionState
from .utils import now_iso, usage_to_public, workflow_context_from_meta


@dataclass(slots=True)
class PublicStreamProjector:
    """Stateful projection from internal AgentStreamEvent -> public SSE events (v1)."""

    stream_id: str
    max_chunk_chars: int = 131_072  # ~128KiB base64/text chunks for chunk.delta events

    _state: ProjectionState = field(default_factory=ProjectionState)

    @staticmethod
    def new_stream_id(*, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex}"

    def _next_event_id(self) -> int:
        self._state.event_id += 1
        return self._state.event_id

    def project(
        self,
        event: AgentStreamEvent,
        *,
        conversation_id: str,
        response_id: str | None,
        agent: str | None,
        workflow_meta: Mapping[str, Any] | None,
        server_timestamp: str | None = None,
    ) -> list[PublicSseEventBase]:
        if self._state.terminal_emitted:
            return []

        ts = server_timestamp or now_iso()
        workflow = workflow_context_from_meta(workflow_meta)
        builder = EventBuilder(
            stream_id=self.stream_id,
            conversation_id=conversation_id,
            response_id=response_id,
            agent=agent,
            workflow=workflow,
            server_timestamp=ts,
            schema=PUBLIC_SSE_SCHEMA_VERSION,
            next_event_id=self._next_event_id,
        )

        apply_attachments(self._state, event)

        out: list[PublicSseEventBase] = []
        if agent and self._state.current_agent is None:
            self._state.current_agent = agent

        out.extend(project_agent_update_event(self._state, builder, event))
        out.extend(
            project_raw_event(
                self._state,
                builder,
                event,
                max_chunk_chars=self.max_chunk_chars,
            )
        )
        if self._state.terminal_emitted:
            return out

        out.extend(project_run_item_event(self._state, builder, event))

        if agent:
            self._state.current_agent = agent

        if event.is_terminal:
            out.append(
                FinalEvent(
                    **builder.base(kind="final"),
                    final=FinalPayload(
                        status=terminal_final_status(self._state, event),
                        response_text=event.response_text,
                        structured_output=event.structured_output,
                        reasoning_summary_text=self._state.reasoning_summary_text or None,
                        refusal_text=self._state.refusal_text or None,
                        attachments=list(self._state.attachments),
                        usage=usage_to_public(event.usage),
                    ),
                )
            )
            self._state.terminal_emitted = True

        return out

    def project_error(
        self,
        *,
        conversation_id: str,
        response_id: str | None,
        agent: str | None,
        workflow_meta: Mapping[str, Any] | None,
        code: str | None,
        message: str,
        source: Literal["provider", "server"],
        is_retryable: bool,
        server_timestamp: str | None = None,
    ) -> ErrorEvent:
        ts = server_timestamp or now_iso()
        workflow = workflow_context_from_meta(workflow_meta)
        self._state.event_id += 1
        self._state.terminal_emitted = True
        return ErrorEvent(
            schema=PUBLIC_SSE_SCHEMA_VERSION,
            kind="error",
            event_id=self._state.event_id,
            stream_id=self.stream_id,
            server_timestamp=ts,
            conversation_id=conversation_id,
            response_id=response_id,
            agent=agent,
            workflow=workflow,
            error=ErrorPayload(
                code=code,
                message=message,
                source=source,
                is_retryable=is_retryable,
            ),
        )
