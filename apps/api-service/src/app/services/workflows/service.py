from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from typing import Any

from app.api.v1.shared.attachments import InputAttachment
from app.core.settings import get_settings
from app.domain.workflows import WorkflowRunListPage, WorkflowRunRepository, WorkflowStatus
from app.observability.metrics import WORKFLOW_RUN_DELETES_TOTAL
from app.services.agents.attachments import AttachmentService
from app.services.agents.context import ConversationActorContext
from app.services.agents.input_attachments import InputAttachmentService
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.provider_registry import (
    AgentProviderRegistry,
    get_provider_registry,
)
from app.services.assets.service import AssetService
from app.services.workflows.catalog import WorkflowCatalogPage, WorkflowCatalogService
from app.services.workflows.runner import WorkflowRunner, WorkflowRunResult
from app.workflows._shared.registry import WorkflowRegistry, get_workflow_registry
from app.workflows._shared.specs import WorkflowDescriptor, WorkflowSpec


@dataclass(slots=True)
class WorkflowRunRequest:
    message: str
    attachments: list[InputAttachment] | None = None
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
        catalog_service: WorkflowCatalogService | None = None,
        attachment_service: AttachmentService | None = None,
        input_attachment_service: InputAttachmentService | None = None,
        asset_service: AssetService | None = None,
    ) -> None:
        self._registry = registry or get_workflow_registry()
        self._catalog_service = catalog_service or WorkflowCatalogService(self._registry)
        self._runner = WorkflowRunner(
            registry=self._registry,
            provider_registry=provider_registry,
            interaction_builder=interaction_builder,
            run_repository=run_repository,
            cancellation_tracker=_CancellationTracker(),
            attachment_service=attachment_service,
            input_attachment_service=input_attachment_service,
            asset_service=asset_service,
        )

    def list_workflows(self) -> Sequence[WorkflowDescriptor]:
        return self._catalog_service.list_workflows()

    def list_workflows_page(
        self, *, limit: int | None, cursor: str | None, search: str | None
    ) -> WorkflowCatalogPage:
        """Paginated workflow catalog listing."""

        return self._catalog_service.list_workflows_page(
            limit=limit,
            cursor=cursor,
            search=search,
        )

    def get_workflow_spec(self, key: str) -> WorkflowSpec:
        spec = self._registry.get(key)
        if spec is None:
            raise ValueError(f"Workflow '{key}' not found")
        return spec

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
            attachments=request.attachments,
            conversation_id=conversation_id,
            location=request.location,
            share_location=request.share_location,
        )

    async def get_run(self, run_id: str):
        if not self._runner._run_repository:
            raise RuntimeError("Workflow run repository is not configured")
        return await self._runner._run_repository.get_run_with_steps(run_id)

    async def list_runs(
        self,
        *,
        tenant_id: str,
        workflow_key: str | None = None,
        status: WorkflowStatus | None = None,
        started_before: datetime | None = None,
        started_after: datetime | None = None,
        conversation_id: str | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> WorkflowRunListPage:
        if not self._runner._run_repository:
            raise RuntimeError("Workflow run repository is not configured")
        return await self._runner._run_repository.list_runs(
            tenant_id=tenant_id,
            workflow_key=workflow_key,
            status=status,
            started_before=started_before,
            started_after=started_after,
            conversation_id=conversation_id,
            cursor=cursor,
            limit=limit,
        )

    async def cancel_run(self, run_id: str, *, tenant_id: str) -> None:
        if not self._runner._run_repository:
            raise RuntimeError("Workflow run repository is not configured")
        run, _ = await self._runner._run_repository.get_run_with_steps(run_id)
        if run.tenant_id != tenant_id:
            raise ValueError("Workflow run not found")
        if run.status != "running":
            raise RuntimeError("Workflow run is not active")
        self._runner.flag_cancel(run_id)
        now = datetime.now(tz=timezone.utc)  # noqa: UP017
        await self._runner._run_repository.cancel_running_steps(run_id, ended_at=now)
        await self._runner._run_repository.cancel_run(run_id, ended_at=now)

    async def delete_run(
        self,
        run_id: str,
        *,
        tenant_id: str,
        user_id: str,
        hard: bool = False,
        reason: str | None = None,
    ) -> None:
        logger = logging.getLogger("app.services.workflows")
        if not self._runner._run_repository:
            raise RuntimeError("Workflow run repository is not configured")

        action = "hard" if hard else "soft"

        try:
            run, _ = await self._runner._run_repository.get_run_with_steps(
                run_id, include_deleted=True
            )
        except ValueError:
            WORKFLOW_RUN_DELETES_TOTAL.labels(action=action, result="not_found").inc()
            logger.info(
                "workflow_run.delete",
                extra={
                    "structured": {
                        "event": "workflow_run.delete",
                        "result": "not_found",
                        "action": action,
                        "workflow_run_id": run_id,
                        "tenant_id": tenant_id,
                        "reason": reason,
                    }
                },
            )
            raise

        if run.tenant_id != tenant_id:
            WORKFLOW_RUN_DELETES_TOTAL.labels(action=action, result="not_found").inc()
            logger.info(
                "workflow_run.delete",
                extra={
                    "structured": {
                        "event": "workflow_run.delete",
                        "result": "not_found",
                        "action": action,
                        "workflow_run_id": run_id,
                        "tenant_id": tenant_id,
                        "reason": "tenant_mismatch",
                    }
                },
            )
            raise ValueError("Workflow run not found")

        if hard:
            settings = get_settings()
            guard_hours = getattr(settings, "workflow_min_purge_age_hours", 0) or 0
            if guard_hours > 0 and run.started_at:
                age_hours = (datetime.now(tz=UTC) - run.started_at).total_seconds() / 3600
                if age_hours < guard_hours:
                    WORKFLOW_RUN_DELETES_TOTAL.labels(action=action, result="blocked").inc()
                    logger.warning(
                        "workflow_run.delete",
                        extra={
                            "structured": {
                                "event": "workflow_run.delete",
                                "result": "blocked",
                                "action": action,
                                "workflow_run_id": run_id,
                                "tenant_id": tenant_id,
                                "reason": "retention_guard",
                                "guard_hours": guard_hours,
                                "run_started_at": run.started_at,
                            }
                        },
                    )
                    raise RuntimeError("Hard delete blocked by retention window")
            await self._runner._run_repository.hard_delete_run(run_id, tenant_id=tenant_id)
            WORKFLOW_RUN_DELETES_TOTAL.labels(action=action, result="success").inc()
            logger.info(
                "workflow_run.delete",
                extra={
                    "structured": {
                        "event": "workflow_run.delete",
                        "result": "success",
                        "action": action,
                        "workflow_run_id": run_id,
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "reason": reason,
                    }
                },
            )
            return

        if run.deleted_at:
            # Already deleted; treat as 404 to avoid leaking existence.
            WORKFLOW_RUN_DELETES_TOTAL.labels(action=action, result="not_found").inc()
            logger.info(
                "workflow_run.delete",
                extra={
                    "structured": {
                        "event": "workflow_run.delete",
                        "result": "not_found",
                        "action": action,
                        "workflow_run_id": run_id,
                        "tenant_id": tenant_id,
                        "reason": "already_deleted",
                    }
                },
            )
            raise ValueError("Workflow run not found")

        await self._runner._run_repository.soft_delete_run(
            run_id, tenant_id=tenant_id, deleted_by=user_id, reason=reason
        )
        WORKFLOW_RUN_DELETES_TOTAL.labels(action=action, result="success").inc()
        logger.info(
            "workflow_run.delete",
            extra={
                "structured": {
                    "event": "workflow_run.delete",
                    "result": "success",
                    "action": action,
                    "workflow_run_id": run_id,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "reason": reason,
                }
            },
        )

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
            attachments=request.attachments,
            conversation_id=conversation_id,
            location=request.location,
            share_location=request.share_location,
        )


def build_workflow_service(
    *,
    run_repository: WorkflowRunRepository | None = None,
    container_service=None,
    vector_store_service=None,
    attachment_service: AttachmentService | None = None,
    input_attachment_service: InputAttachmentService | None = None,
) -> WorkflowService:
    return WorkflowService(
        registry=get_workflow_registry(),
        provider_registry=get_provider_registry(),
        interaction_builder=InteractionContextBuilder(
            container_service=container_service, vector_store_service=vector_store_service
        ),
        run_repository=run_repository,
        attachment_service=attachment_service,
        input_attachment_service=input_attachment_service,
    )


def get_workflow_service() -> WorkflowService:
    from app.bootstrap.container import get_container, wire_workflow_services

    container = get_container()
    wire_workflow_services(container)
    if container.workflow_service is None:  # pragma: no cover - defensive
        raise RuntimeError("WorkflowService was not configured")
    return container.workflow_service


__all__ = [
    "WorkflowService",
    "get_workflow_service",
    "build_workflow_service",
    "WorkflowRunRequest",
]


class _CancellationTracker(set[str]):
    """Simple shared cancellation flag set."""

    def flag(self, run_id: str) -> None:
        self.add(run_id)

    def is_cancelled(self, run_id: str) -> bool:
        return run_id in self
