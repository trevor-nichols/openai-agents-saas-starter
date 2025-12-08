"""Workflow catalog and execution endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.v1.shared.stream_normalizer import normalize_stream_event
from app.api.v1.workflows.schemas import (
    StreamingWorkflowEvent,
    WorkflowDescriptorResponse,
    WorkflowRunDetail,
    WorkflowRunListItem,
    WorkflowRunListResponse,
    WorkflowRunRequestBody,
    WorkflowRunResponse,
    WorkflowStageDescriptor,
    WorkflowStepDescriptor,
    WorkflowStepResultSchema,
    WorkflowSummary,
)
from app.domain.workflows import WorkflowStatus
from app.services.agents.context import ConversationActorContext
from app.services.workflows.service import WorkflowRunRequest, get_workflow_service
from app.workflows._shared.schema_utils import schema_to_json_schema

router = APIRouter(prefix="/workflows", tags=["workflows"])
_ALLOWED_ROLES: tuple[TenantRole, ...] = (
    TenantRole.VIEWER,
    TenantRole.ADMIN,
    TenantRole.OWNER,
)
_ADMIN_ROLES: tuple[TenantRole, ...] = (TenantRole.ADMIN, TenantRole.OWNER)


@router.get("", response_model=list[WorkflowSummary])
async def list_workflows(
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_context: TenantContext = Depends(require_tenant_role(*_ALLOWED_ROLES)),
):
    service = get_workflow_service()
    return [
        WorkflowSummary(
            key=desc.key,
            display_name=desc.display_name,
            description=desc.description,
            step_count=desc.step_count,
            default=desc.default,
        )
        for desc in service.list_workflows()
    ]


@router.post("/{workflow_key}/run", response_model=WorkflowRunResponse)
async def run_workflow(
    workflow_key: str,
    request: WorkflowRunRequestBody,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:write")),
    tenant_context: TenantContext = Depends(require_tenant_role(*_ALLOWED_ROLES)),
):
    service = get_workflow_service()
    user_id = current_user.get("user_id") or current_user.get("subject")
    actor = ConversationActorContext(
        tenant_id=tenant_context.tenant_id,
        user_id=str(user_id),
    )
    try:
        result = await service.run_workflow(
            workflow_key,
            request=WorkflowRunRequest(
                message=request.message,
                conversation_id=request.conversation_id,
                location=request.location,
                share_location=request.share_location,
            ),
            actor=actor,
        )
    except ValueError as exc:
        message = str(exc)
        if "not found" in message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    return WorkflowRunResponse(
        workflow_key=result.workflow_key,
        workflow_run_id=result.workflow_run_id,
        conversation_id=result.conversation_id,
        steps=[
            WorkflowStepResultSchema(
                name=step.name,
                agent_key=step.agent_key,
                response_text=step.response.response_text,
                structured_output=step.response.structured_output,
                response_id=step.response.response_id,
                stage_name=step.stage_name,
                parallel_group=step.parallel_group,
                branch_index=step.branch_index,
                output_schema=step.output_schema,
            )
            for step in result.steps
        ],
        final_output=result.final_output,
        output_schema=result.output_schema,
    )


@router.get("/runs", response_model=WorkflowRunListResponse)
async def list_workflow_runs(
    workflow_key: str | None = Query(None, description="Filter by workflow key."),
    run_status: str | None = Query(None, description="Filter by workflow status."),
    started_before: str | None = Query(
        None, description="Return runs that started at or before this ISO timestamp."
    ),
    started_after: str | None = Query(
        None, description="Return runs that started at or after this ISO timestamp."
    ),
    conversation_id: str | None = Query(None, description="Filter by conversation id."),
    cursor: str | None = Query(None, description="Opaque pagination cursor."),
    limit: int = Query(20, ge=1, le=100, description="Maximum runs to return."),
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_context: TenantContext = Depends(require_tenant_role(*_ALLOWED_ROLES)),
):
    service = get_workflow_service()
    try:
        page = await service.list_runs(
            tenant_id=tenant_context.tenant_id,
            workflow_key=workflow_key,
            status=_parse_status(run_status),
            started_before=_parse_iso(started_before),
            started_after=_parse_iso(started_after),
            conversation_id=conversation_id,
            cursor=cursor,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    items = [
        WorkflowRunListItem(
            workflow_run_id=item.id,
            workflow_key=item.workflow_key,
            status=item.status,
            started_at=item.started_at.isoformat(),
            ended_at=item.ended_at.isoformat() if item.ended_at else None,
            user_id=item.user_id,
            conversation_id=item.conversation_id,
            step_count=item.step_count,
            duration_ms=item.duration_ms,
            final_output_text=item.final_output_text,
        )
        for item in page.items
    ]
    return WorkflowRunListResponse(items=items, next_cursor=page.next_cursor)


@router.get("/runs/{run_id}", response_model=WorkflowRunDetail)
async def get_workflow_run(
    run_id: str,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_context: TenantContext = Depends(require_tenant_role(*_ALLOWED_ROLES)),
):
    service = get_workflow_service()
    try:
        run, steps = await service.get_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if run.tenant_id != tenant_context.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")

    spec = None
    try:
        spec = service.get_workflow_spec(run.workflow_key)
    except ValueError:
        spec = None
    step_schemas = _align_step_schemas(spec, steps) if spec else [None] * len(steps)
    workflow_schema = schema_to_json_schema(spec.output_schema) if spec else None

    return WorkflowRunDetail(
        workflow_key=run.workflow_key,
        workflow_run_id=run.id,
        tenant_id=run.tenant_id,
        user_id=run.user_id,
        status=run.status,
        started_at=run.started_at.isoformat(),
        ended_at=run.ended_at.isoformat() if run.ended_at else None,
        final_output_text=run.final_output_text,
        final_output_structured=run.final_output_structured,
        request_message=run.request_message,
        conversation_id=run.conversation_id,
        output_schema=workflow_schema,
        steps=[
            WorkflowStepResultSchema(
                name=step.step_name,
                agent_key=step.step_agent,
                response_text=step.response_text,
                structured_output=step.structured_output,
                response_id=step.response_id,
                stage_name=step.stage_name,
                parallel_group=step.parallel_group,
                branch_index=step.branch_index,
                output_schema=step_schemas[idx] if idx < len(step_schemas) else None,
            )
            for idx, step in enumerate(steps)
        ],
    )


@router.post("/runs/{run_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_workflow_run(
    run_id: str,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:write")),
    tenant_context: TenantContext = Depends(require_tenant_role(*_ALLOWED_ROLES)),
):
    service = get_workflow_service()
    try:
        await service.cancel_run(run_id, tenant_id=tenant_context.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {"success": True}


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_run(
    run_id: str,
    hard: bool = Query(
        False,
        description="If true, permanently deletes the run and steps (subject to retention guard).",
    ),
    reason: str | None = Query(
        None,
        description="Optional audit reason for deletion.",
    ),
    current_user: CurrentUser = Depends(require_verified_scopes("workflows:delete")),
    tenant_context: TenantContext = Depends(require_tenant_role(*_ADMIN_ROLES)),
):
    service = get_workflow_service()
    user_id = str(current_user.get("user_id") or current_user.get("subject") or "unknown")
    try:
        await service.delete_run(
            run_id,
            tenant_id=tenant_context.tenant_id,
            user_id=user_id,
            hard=hard,
            reason=reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return None


STREAM_EVENT_RESPONSE = {
    "description": "Server-sent events stream of workflow outputs.",
    "model": StreamingWorkflowEvent,
    "content": {
        "text/event-stream": {
            "schema": {"$ref": "#/components/schemas/StreamingWorkflowEvent"}
        }
    },
}


@router.post("/{workflow_key}/run-stream", responses={200: STREAM_EVENT_RESPONSE})
async def run_workflow_stream(
    workflow_key: str,
    request: WorkflowRunRequestBody,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:write")),
    tenant_context: TenantContext = Depends(require_tenant_role(*_ALLOWED_ROLES)),
):
    service = get_workflow_service()
    user_id = current_user.get("user_id") or current_user.get("subject")
    actor = ConversationActorContext(
        tenant_id=tenant_context.tenant_id,
        user_id=str(user_id),
    )

    try:
        stream = await service.run_workflow_stream(
            workflow_key,
            request=WorkflowRunRequest(
                message=request.message,
                conversation_id=request.conversation_id,
                location=request.location,
                share_location=request.share_location,
            ),
            actor=actor,
        )
    except ValueError as exc:
        message = str(exc)
        if "not found" in message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
        ) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    async def _event_stream():
        event_id = 0
        last_heartbeat = datetime.now(tz=UTC)

        try:
            async for event in stream:
                metadata = event.metadata if isinstance(event.metadata, dict) else {}
                now_iso = datetime.now(tz=UTC).isoformat()
                payload = normalize_stream_event(
                    event,
                    workflow_meta={
                        "workflow_key": metadata.get("workflow_key", workflow_key),
                        "workflow_run_id": metadata.get("workflow_run_id"),
                        "step_name": metadata.get("step_name"),
                        "step_agent": metadata.get("step_agent"),
                        "stage_name": metadata.get("stage_name"),
                        "parallel_group": metadata.get("parallel_group"),
                        "branch_index": metadata.get("branch_index"),
                    },
                    default_conversation_id=event.conversation_id,
                    server_timestamp=now_iso,
                )
                event_id += 1
                yield f"id: {event_id}\nevent: {event.kind}\ndata: {payload.model_dump_json()}\n\n"

                now = datetime.now(tz=UTC)
                if (now - last_heartbeat).total_seconds() >= 15:
                    last_heartbeat = now
                    yield f": heartbeat {now.isoformat()}\n\n"
        except Exception as exc:
            error_payload = StreamingWorkflowEvent(
                kind="error",
                workflow_key=workflow_key,
                conversation_id=request.conversation_id or "unknown",
                agent_used=None,
                response_id=None,
                sequence_number=None,
                raw_type=None,
                run_item_name=None,
                run_item_type=None,
                tool_call_id=None,
                tool_name=None,
                agent=None,
                new_agent=None,
                text_delta=None,
                reasoning_delta=None,
                response_text=None,
                is_terminal=True,
                payload={"error": str(exc)},
                server_timestamp=datetime.now(tz=UTC).isoformat(),
            )
            event_id += 1
            yield f"id: {event_id}\nevent: error\ndata: {error_payload.model_dump_json()}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
    }

    return StreamingResponse(_event_stream(), media_type="text/event-stream", headers=headers)


@router.get("/{workflow_key}", response_model=WorkflowDescriptorResponse)
async def get_workflow_descriptor(
    workflow_key: str,
    current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
    tenant_context: TenantContext = Depends(require_tenant_role(*_ALLOWED_ROLES)),
):
    service = get_workflow_service()
    try:
        spec = service.get_workflow_spec(workflow_key)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    stages = []
    for stage in spec.resolved_stages():
        steps = [
            WorkflowStepDescriptor(
                name=step.display_name(),
                agent_key=step.agent_key,
                guard=step.guard,
                guard_type=step.guard_type,
                input_mapper=step.input_mapper,
                input_mapper_type=step.input_mapper_type,
                max_turns=step.max_turns,
                output_schema=schema_to_json_schema(step.output_schema),
            )
            for step in stage.steps
        ]
        stages.append(
            WorkflowStageDescriptor(
                name=stage.name,
                mode=stage.mode,
                reducer=stage.reducer,
                steps=steps,
            )
        )

    return WorkflowDescriptorResponse(
        key=spec.key,
        display_name=spec.display_name,
        description=spec.description,
        default=spec.default,
        allow_handoff_agents=spec.allow_handoff_agents,
        step_count=spec.step_count,
        stages=stages,
        output_schema=schema_to_json_schema(spec.output_schema),
    )


def _parse_iso(value: str | None):
    if value is None:
        return None
    try:
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        dt = datetime.fromisoformat(normalized)
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
    except ValueError as exc:  # pragma: no cover - invalid user input
        raise ValueError("Invalid datetime format; use ISO-8601") from exc


def _parse_status(value: str | None) -> WorkflowStatus | None:
    if value is None:
        return None
    allowed: tuple[WorkflowStatus, ...] = ("running", "succeeded", "failed", "cancelled")
    if value not in allowed:
        raise ValueError("Invalid status filter.")
    return cast(WorkflowStatus, value)


def _align_step_schemas(spec, steps) -> list[dict[str, Any] | None]:
    # Build a cursor over the declared steps to align schemas with executed steps,
    # preserving execution order and handling duplicate names/guards.
    declared: list[tuple[str, dict[str, Any] | None]] = []
    for stage in spec.resolved_stages():
        for step in stage.steps:
            declared.append((step.display_name(), schema_to_json_schema(step.output_schema)))

    aligned: list[dict[str, Any] | None] = []
    cursor = 0
    for step in steps:
        schema = None
        while cursor < len(declared):
            name, maybe_schema = declared[cursor]
            cursor += 1
            if name == step.step_name:
                schema = maybe_schema
                break
        aligned.append(schema)
    return aligned
