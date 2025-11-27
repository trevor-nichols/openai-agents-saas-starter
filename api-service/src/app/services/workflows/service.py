from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any

from app.domain.workflows import WorkflowRunRepository
from app.services.agents.context import ConversationActorContext
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.provider_registry import (
    AgentProviderRegistry,
    get_provider_registry,
)
from app.services.workflows.runner import WorkflowRunner, WorkflowRunResult
from app.workflows.registry import WorkflowRegistry, get_workflow_registry
from app.workflows.specs import WorkflowDescriptor


@dataclass(slots=True)
class WorkflowRunRequest:
    message: str
    conversation_id: str | None = None
    location: Any | None = None
    share_location: bool | None = None


class WorkflowService:
    def __init__(
        self,
        *,
        registry: WorkflowRegistry | None = None,
        provider_registry: AgentProviderRegistry | None = None,
        interaction_builder: InteractionContextBuilder | None = None,
        run_repository: WorkflowRunRepository | None = None,
    ) -> None:
        self._registry = registry or get_workflow_registry()
        self._runner = WorkflowRunner(
            registry=self._registry,
            provider_registry=provider_registry,
            interaction_builder=interaction_builder,
            run_repository=run_repository,
        )

    def list_workflows(self) -> Sequence[WorkflowDescriptor]:
        return self._registry.list_descriptors()

    async def run_workflow(
        self,
        key: str,
        *,
        request: WorkflowRunRequest,
        actor: ConversationActorContext,
    ) -> WorkflowRunResult:
        spec = self._registry.get(key)
        if spec is None:
            raise ValueError(f"Workflow '{key}' not found")

        conversation_id = request.conversation_id or str(uuid.uuid4())
        return await self._runner.run(
            spec,
            actor=actor,
            message=request.message,
            conversation_id=conversation_id,
            location=request.location,
            share_location=request.share_location,
        )

    async def get_run(self, run_id: str):
        if not self._runner._run_repository:
            raise RuntimeError("Workflow run repository is not configured")
        return await self._runner._run_repository.get_run_with_steps(run_id)

    async def run_workflow_stream(
        self,
        key: str,
        *,
        request: WorkflowRunRequest,
        actor: ConversationActorContext,
    ) -> AsyncIterator[Any]:
        spec = self._registry.get(key)
        if spec is None:
            raise ValueError(f"Workflow '{key}' not found")

        conversation_id = request.conversation_id or str(uuid.uuid4())
        return self._runner.run_stream(
            spec,
            actor=actor,
            message=request.message,
            conversation_id=conversation_id,
            location=request.location,
            share_location=request.share_location,
        )


def build_workflow_service(
    *,
    run_repository: WorkflowRunRepository | None = None,
    container_service=None,
) -> WorkflowService:
    return WorkflowService(
        registry=get_workflow_registry(),
        provider_registry=get_provider_registry(),
        interaction_builder=InteractionContextBuilder(container_service=container_service),
        run_repository=run_repository,
    )


def get_workflow_service() -> WorkflowService:
    from app.bootstrap.container import get_container, wire_container_service
    from app.infrastructure.persistence.workflows.repository import (
        SqlAlchemyWorkflowRunRepository,
    )

    container = get_container()
    if container.workflow_run_repository is None:
        if container.session_factory is None:
            raise RuntimeError("Session factory must be configured before workflow services")
        container.workflow_run_repository = SqlAlchemyWorkflowRunRepository(
            container.session_factory
        )

    if container.container_service is None:
        wire_container_service(container)

    if container.workflow_service is None:
        container.workflow_service = build_workflow_service(
            run_repository=container.workflow_run_repository,
            container_service=container.container_service,
        )
    return container.workflow_service


__all__ = [
    "WorkflowService",
    "get_workflow_service",
    "build_workflow_service",
    "WorkflowRunRequest",
]
