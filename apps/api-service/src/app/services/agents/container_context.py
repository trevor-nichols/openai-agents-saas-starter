"""Resolve and persist code interpreter container context for run auditing."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from app.agents._shared.prompt_context import ContainerOverrideContext, PromptRuntimeContext
from app.agents._shared.registry_loader import load_agent_specs
from app.domain.conversations import ConversationEvent
from app.services.containers import ContainerNotFoundError, ContainerService

logger = logging.getLogger(__name__)

ContainerContextPayload = dict[str, str | None]


class ContainerContextService:
    """Computes effective container context for agents and persists run events."""

    def __init__(
        self,
        *,
        container_service: ContainerService | None = None,
        spec_loader: Callable[[], Iterable[Any]] = load_agent_specs,
    ) -> None:
        self._container_service = container_service
        self._spec_loader = spec_loader
        self._spec_index: dict[str, Any] | None = None

    async def resolve_contexts(
        self,
        *,
        agent_keys: Iterable[str],
        runtime_ctx: PromptRuntimeContext | None,
        tenant_id: str,
    ) -> dict[str, ContainerContextPayload]:
        contexts: dict[str, ContainerContextPayload] = {}
        specs = self._load_specs()
        for agent_key in agent_keys:
            spec = specs.get(agent_key)
            if spec is None or "code_interpreter" not in getattr(spec, "tool_keys", ()):
                continue
            context = await self._resolve_for_agent(
                spec=spec,
                agent_key=agent_key,
                runtime_ctx=runtime_ctx,
                tenant_id=tenant_id,
            )
            if context:
                contexts[agent_key] = context
        return contexts

    async def build_run_events(
        self,
        *,
        agent_keys: Iterable[str],
        runtime_ctx: PromptRuntimeContext | None,
        tenant_id: str,
        response_id: str | None = None,
        workflow_run_id: str | None = None,
    ) -> list[ConversationEvent]:
        contexts = await self.resolve_contexts(
            agent_keys=agent_keys,
            runtime_ctx=runtime_ctx,
            tenant_id=tenant_id,
        )
        return self.build_run_events_from_contexts(
            contexts,
            response_id=response_id,
            workflow_run_id=workflow_run_id,
        )

    async def append_run_events(
        self,
        *,
        conversation_service,
        conversation_id: str,
        tenant_id: str,
        agent_keys: Iterable[str],
        runtime_ctx: PromptRuntimeContext | None,
        response_id: str | None = None,
        workflow_run_id: str | None = None,
    ) -> None:
        events = await self.build_run_events(
            agent_keys=agent_keys,
            runtime_ctx=runtime_ctx,
            tenant_id=tenant_id,
            response_id=response_id,
            workflow_run_id=workflow_run_id,
        )
        if not events:
            return
        await conversation_service.append_run_events(
            conversation_id,
            tenant_id=tenant_id,
            events=events,
        )

    async def build_metadata_payload(
        self,
        *,
        agent_keys: Iterable[str],
        runtime_ctx: PromptRuntimeContext | None,
        tenant_id: str,
    ) -> dict[str, Any] | None:
        contexts = await self.resolve_contexts(
            agent_keys=agent_keys,
            runtime_ctx=runtime_ctx,
            tenant_id=tenant_id,
        )
        return self.build_metadata_from_contexts(contexts)

    @staticmethod
    def build_run_events_from_contexts(
        contexts: Mapping[str, ContainerContextPayload],
        *,
        response_id: str | None,
        workflow_run_id: str | None,
    ) -> list[ConversationEvent]:
        if not contexts:
            return []
        events: list[ConversationEvent] = []
        for agent_key, context in contexts.items():
            events.append(
                ConversationEvent(
                    run_item_type="tool_context",
                    run_item_name="code_interpreter",
                    agent=agent_key,
                    call_output={"container_context": context},
                    response_id=response_id,
                    workflow_run_id=workflow_run_id,
                )
            )
        return events

    @staticmethod
    def build_metadata_from_contexts(
        contexts: Mapping[str, ContainerContextPayload],
    ) -> dict[str, Any] | None:
        if not contexts:
            return None
        return {"container_context": dict(contexts)}

    async def _resolve_for_agent(
        self,
        *,
        spec,
        agent_key: str,
        runtime_ctx: PromptRuntimeContext | None,
        tenant_id: str,
    ) -> ContainerContextPayload | None:
        override_context = None
        if runtime_ctx and runtime_ctx.container_overrides:
            override_context = runtime_ctx.container_overrides.get(agent_key)
        if override_context:
            container_id, openai_container_id = _coerce_override(override_context)
            return {
                "source": "override",
                "container_id": container_id,
                "openai_container_id": openai_container_id,
            }

        config = None
        if isinstance(getattr(spec, "tool_configs", None), Mapping):
            config = spec.tool_configs.get("code_interpreter")
        if isinstance(config, Mapping) and config.get("container_id"):
            openai_container_id = str(config["container_id"])
            container_id = await self._resolve_local_container_id(
                openai_container_id=openai_container_id,
                tenant_id=tenant_id,
            )
            return {
                "source": "spec",
                "container_id": container_id,
                "openai_container_id": openai_container_id,
            }

        openai_container_id = None
        if runtime_ctx and runtime_ctx.container_bindings:
            openai_container_id = runtime_ctx.container_bindings.get(agent_key)
        if openai_container_id:
            container_id = await self._resolve_local_container_id(
                openai_container_id=openai_container_id,
                tenant_id=tenant_id,
            )
            return {
                "source": "binding",
                "container_id": container_id,
                "openai_container_id": openai_container_id,
            }

        return {
            "source": "auto",
            "container_id": None,
            "openai_container_id": None,
        }

    async def _resolve_local_container_id(
        self,
        *,
        openai_container_id: str,
        tenant_id: str,
    ) -> str | None:
        if not self._container_service:
            return None
        try:
            tenant_uuid = uuid.UUID(str(tenant_id))
        except Exception:
            return None
        try:
            container = await self._container_service.get_container_by_openai_id(
                openai_container_id=openai_container_id,
                tenant_id=tenant_uuid,
            )
        except ContainerNotFoundError:
            return None
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug(
                "container_context.resolve.failed",
                exc_info=exc,
                extra={"tenant_id": tenant_id, "openai_container_id": openai_container_id},
            )
            return None
        return str(container.id)

    def _load_specs(self) -> dict[str, Any]:
        if self._spec_index is None:
            self._spec_index = {spec.key: spec for spec in self._spec_loader()}
        return self._spec_index


def _coerce_override(value: Any) -> tuple[str | None, str | None]:
    if isinstance(value, ContainerOverrideContext):
        return value.container_id, value.openai_container_id
    if isinstance(value, Mapping):
        return (
            _maybe_str(value.get("container_id")),
            _maybe_str(value.get("openai_container_id") or value.get("openai_id")),
        )
    if isinstance(value, str):
        return None, value
    return None, None


def _maybe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


__all__ = ["ContainerContextService", "ContainerContextPayload"]
