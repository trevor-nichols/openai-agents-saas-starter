from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping, Sequence

from app.domain.ai.models import AgentDescriptor, AgentRunResult, AgentRunUsage, AgentStreamEvent
from app.domain.ai.ports import AgentProvider, AgentRuntime, AgentSessionStore, AgentStreamingHandle


class _StubSessionHandle:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._items: list[Mapping[str, Any]] = []

    def get_items(self) -> list[Mapping[str, Any]]:
        return list(self._items)

    def add_items(self, items: Sequence[Mapping[str, Any]]) -> None:
        self._items.extend(items)


class StubSessionStore(AgentSessionStore):
    def build(self, session_id: str) -> _StubSessionHandle:
        return _StubSessionHandle(session_id)


class _StubStreamingHandle(AgentStreamingHandle):
    def __init__(
        self,
        events: Sequence[AgentStreamEvent],
        usage: AgentRunUsage | None = None,
    ) -> None:
        self._events = list(events)
        self._usage = usage
        self._last_response_id = self._events[-1].response_id if self._events else None

    async def events(self):
        for event in self._events:
            yield event

    @property
    def last_response_id(self) -> str | None:  # pragma: no cover - simple accessor
        return self._last_response_id

    @property
    def usage(self) -> AgentRunUsage | None:  # pragma: no cover - simple accessor
        return self._usage


class StubRuntime(AgentRuntime):
    def __init__(self, default_agent: str) -> None:
        self._default_agent = default_agent

    async def run(
        self,
        agent_key: str,
        message: Any,
        *,
        session: Any | None = None,
        conversation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: Any | None = None,
    ) -> AgentRunResult:
        text = _coerce_message_text(message)
        response_text = f"Stub response: {text}" if text else "Stub response."
        return AgentRunResult(
            final_output=response_text,
            response_id=f"resp_stub_{uuid.uuid4().hex}",
            usage=AgentRunUsage(requests=1),
            response_text=response_text,
            final_agent=agent_key or self._default_agent,
        )

    def run_stream(
        self,
        agent_key: str,
        message: Any,
        *,
        session: Any | None = None,
        conversation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: Any | None = None,
    ) -> AgentStreamingHandle:
        response_id = f"resp_stub_{uuid.uuid4().hex}"
        response_text = f"Stub stream response: {_coerce_message_text(message)}".strip()
        events = [
            AgentStreamEvent(
                kind="run_item_stream_event",
                response_id=response_id,
                response_text=response_text or "Stub stream response.",
                is_terminal=True,
            )
        ]
        return _StubStreamingHandle(events, usage=AgentRunUsage(requests=1))


@dataclass(slots=True)
class _StubConversationFactory:
    async def create(self, *args: Any, **kwargs: Any) -> str:
        return f"conv_stub_{uuid.uuid4().hex}"


class StubAgentProvider(AgentProvider):
    name = "stub"

    def __init__(self, descriptors: Sequence[AgentDescriptor], default_key: str) -> None:
        self._descriptors = {desc.key: desc for desc in descriptors}
        self._default_key = default_key
        self._runtime = StubRuntime(default_key)
        self._session_store = StubSessionStore()
        self._conversation_factory = _StubConversationFactory()

    @property
    def runtime(self) -> StubRuntime:
        return self._runtime

    @property
    def session_store(self) -> StubSessionStore:
        return self._session_store

    @property
    def conversation_factory(self) -> _StubConversationFactory:
        return self._conversation_factory

    def list_agents(self):
        return list(self._descriptors.values())

    def resolve_agent(self, preferred_key: str | None = None) -> AgentDescriptor:
        if preferred_key and preferred_key in self._descriptors:
            return self._descriptors[preferred_key]
        return self._descriptors[self._default_key]

    def get_agent(self, agent_key: str) -> AgentDescriptor | None:
        return self._descriptors.get(agent_key)

    def default_agent_key(self) -> str:
        return self._default_key

    def tool_overview(self):
        return {key: [] for key in self._descriptors}

    def mark_seen(self, agent_key: str, ts: datetime) -> None:
        descriptor = self._descriptors.get(agent_key)
        if descriptor is None:
            return
        descriptor.last_seen_at = ts if ts.tzinfo else ts.replace(tzinfo=UTC)


def build_stub_provider() -> StubAgentProvider:
    descriptors = _load_agent_descriptors()
    default_key = next((d.key for d in descriptors if d.key == "triage"), descriptors[0].key)
    return StubAgentProvider(descriptors, default_key)


def _load_agent_descriptors() -> list[AgentDescriptor]:
    try:
        from app.agents._shared.registry_loader import load_agent_specs

        specs = load_agent_specs()
    except Exception:
        return [
            AgentDescriptor(
                key="triage",
                display_name="Triage",
                description="Stub triage agent",
                model="gpt-5-mini",
            ),
            AgentDescriptor(
                key="researcher",
                display_name="Researcher",
                description="Stub researcher agent",
                model="gpt-5-mini",
            ),
            AgentDescriptor(
                key="code_assistant",
                display_name="Code Assistant",
                description="Stub code assistant",
                model="gpt-5-mini",
            ),
        ]

    descriptors: list[AgentDescriptor] = []
    for spec in specs:
        model = spec.model or "gpt-5-mini"
        descriptors.append(
            AgentDescriptor(
                key=spec.key,
                display_name=spec.display_name,
                description=spec.description,
                model=model,
                capabilities=spec.capabilities,
            )
        )
    return descriptors


def _coerce_message_text(message: Any) -> str:
    if isinstance(message, str):
        return message
    if isinstance(message, list):
        parts: list[str] = []
        for item in message:
            if isinstance(item, dict):
                text = item.get("content") or item.get("text")
                if text:
                    parts.append(str(text))
            else:
                parts.append(str(item))
        return " ".join(parts)
    if message is None:
        return ""
    return str(message)


__all__ = ["StubAgentProvider", "build_stub_provider"]
