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
from .state import ProjectionState, ToolState
from .utils import coerce_str, now_iso, usage_to_public, workflow_context_from_meta


@dataclass(slots=True)
class PublicStreamProjector:
    """Stateful projection from internal AgentStreamEvent -> public SSE events (v1)."""

    stream_id: str
    max_chunk_chars: int = 131_072  # ~128KiB base64/text chunks for chunk.delta events

    _state: ProjectionState = field(default_factory=ProjectionState)
    _scoped_states: dict[str, ProjectionState] = field(default_factory=dict)

    @staticmethod
    def new_stream_id(*, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex}"

    def _next_event_id(self) -> int:
        self._state.event_id += 1
        return self._state.event_id

    @staticmethod
    def _scope_payload(event: AgentStreamEvent) -> dict[str, Any] | None:
        scope = event.scope
        if scope is None:
            return None
        if isinstance(scope, Mapping):
            return dict(scope)
        mapped = AgentStreamEvent._to_mapping(scope)
        if isinstance(mapped, Mapping):
            return dict(mapped)
        return None

    @staticmethod
    def _scope_key(scope_payload: Mapping[str, Any] | None) -> str | None:
        if not scope_payload:
            return None
        scope_type = scope_payload.get("type")
        tool_call_id = scope_payload.get("tool_call_id")
        if isinstance(scope_type, str) and isinstance(tool_call_id, str):
            return f"{scope_type}:{tool_call_id}"
        return None

    def _state_for_scope(self, scope_payload: Mapping[str, Any] | None) -> ProjectionState:
        scope_key = self._scope_key(scope_payload)
        if scope_key is None:
            return self._state
        return self._scoped_states.setdefault(scope_key, ProjectionState())

    def _seed_agent_tool_state(self, scope_payload: Mapping[str, Any] | None) -> None:
        if not scope_payload:
            return
        if scope_payload.get("type") != "agent_tool":
            return
        tool_call_id = coerce_str(scope_payload.get("tool_call_id"))
        if not tool_call_id:
            return
        tool_state = self._state.tool_state.setdefault(
            tool_call_id, ToolState(tool_type="agent")
        )
        tool_state.tool_type = "agent"
        tool_state.tool_name = coerce_str(scope_payload.get("tool_name")) or tool_state.tool_name
        tool_state.agent_name = coerce_str(scope_payload.get("agent")) or tool_state.agent_name

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
        scope_payload = self._scope_payload(event)
        self._seed_agent_tool_state(scope_payload)
        state = self._state_for_scope(scope_payload)
        builder = EventBuilder(
            stream_id=self.stream_id,
            conversation_id=conversation_id,
            response_id=response_id,
            agent=agent,
            workflow=workflow,
            scope=scope_payload,
            server_timestamp=ts,
            schema=PUBLIC_SSE_SCHEMA_VERSION,
            next_event_id=self._next_event_id,
        )

        if scope_payload is None:
            apply_attachments(self._state, event)

        out: list[PublicSseEventBase] = []
        if scope_payload is None:
            if agent and self._state.current_agent is None:
                self._state.current_agent = agent
        elif state.current_agent is None:
            scoped_agent = coerce_str(scope_payload.get("agent")) if scope_payload else None
            if scoped_agent:
                state.current_agent = scoped_agent

        out.extend(project_agent_update_event(state, builder, event))
        out.extend(
            project_raw_event(
                state,
                builder,
                event,
                max_chunk_chars=self.max_chunk_chars,
            )
        )
        if state.terminal_emitted:
            return out

        out.extend(project_run_item_event(state, builder, event))

        if scope_payload is None and agent:
            self._state.current_agent = agent

        if event.is_terminal and scope_payload is None:
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
