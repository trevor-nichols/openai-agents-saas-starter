"""Workflow catalog and execution endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.dependencies.tenant import TenantContext, TenantRole, require_tenant_role
from app.api.v1.workflows.schemas import (
    StreamingWorkflowEvent,
    WorkflowRunDetail,
    WorkflowRunRequestBody,
    WorkflowRunResponse,
    WorkflowStepResultSchema,
    WorkflowSummary,
)
from app.services.agents.context import ConversationActorContext
from app.services.workflows.service import WorkflowRunRequest, get_workflow_service

router = APIRouter(prefix="/workflows", tags=["workflows"])
_ALLOWED_ROLES: tuple[TenantRole, ...] = (
    TenantRole.VIEWER,
    TenantRole.ADMIN,
    TenantRole.OWNER,
)


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
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
            )
            for step in result.steps
        ],
        final_output=result.final_output,
    )


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
            )
            for step in steps
        ],
    )


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    async def _event_stream():
        try:
            async for event in stream:
                metadata = event.metadata if isinstance(event.metadata, dict) else {}
                payload = StreamingWorkflowEvent(
                    kind=event.kind,
                    workflow_key=metadata.get("workflow_key", workflow_key),
                    workflow_run_id=metadata.get("workflow_run_id"),
                    step_name=metadata.get("step_name"),
                    step_agent=metadata.get("step_agent"),
                    stage_name=metadata.get("stage_name"),
                    parallel_group=metadata.get("parallel_group"),
                    branch_index=metadata.get("branch_index"),
                    conversation_id=event.conversation_id,
                    agent_used=event.agent,
                    response_id=event.response_id,
                    sequence_number=event.sequence_number,
                    raw_type=event.raw_type,
                    run_item_name=event.run_item_name,
                    run_item_type=event.run_item_type,
                    tool_call_id=event.tool_call_id,
                    tool_name=event.tool_name,
                    agent=event.agent,
                    new_agent=event.new_agent,
                    text_delta=event.text_delta,
                    reasoning_delta=event.reasoning_delta,
                    response_text=event.response_text,
                    structured_output=event.structured_output,
                    is_terminal=event.is_terminal,
                    payload=event.payload if isinstance(event.payload, dict) else None,
                    attachments=event.attachments,
                )
                yield f"data: {payload.model_dump_json()}\n\n"
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
            )
            yield f"data: {error_payload.model_dump_json()}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
    }

    return StreamingResponse(_event_stream(), media_type="text/event-stream", headers=headers)
