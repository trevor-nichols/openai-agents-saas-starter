Workflow services
=================

Runtime layer that takes workflow specs from `app/workflows/**/spec.py`, runs them deterministically, and records results. It sits between the workflow registry and API routers, using the Agents SDK provider runtime under the hood.

What lives here
---------------
- `service.py` — public facade used by API handlers. Lists workflow catalog entries, resolves a `WorkflowSpec`, runs or streams it, surfaces run history, and issues cancel/delete operations.
- `runner.py` — orchestration core. Wraps runs in `agents.trace`, dispatches stages, handles cancellation flags, and coordinates helpers.
- `stages.py` / `streaming.py` — stage executors. Sequential and parallel fan-out/fan-in variants for non-streaming and streaming flows.
- `execution.py` — executes a single step via `provider.runtime.run(...)`, prioritizes structured output → response text → final output, and validates step output against the declared schema.
- `hooks.py` — loads guard/input-mapper/reducer callables from dotted paths (`module:attr` or `module.attr`) and runs them (sync or async).
- `recording.py` — persists runs and steps through the `WorkflowRunRepository`, and emits activity log entries.
- `catalog.py` — read-only workflow catalog with pagination and search backed by the registry.
- `run_context.py` — bootstraps workflow runs (user input resolution, runtime context, recorder start, container context events).
- `attachments.py` — attachment ingestion for workflow runs (streaming + non-streaming).
- `session_events.py` — projects provider session deltas into conversation event logs.
- `output.py` — output formatting, usage aggregation, and assistant message persistence.
- `utils.py` — workflow helper utilities (agent key discovery).
- `types.py` — dataclasses for `WorkflowRunResult` and `WorkflowStepResult`.

Execution flow (non-streaming)
------------------------------
1. API layer calls `WorkflowService.run_workflow` with a workflow key and `WorkflowRunRequest`.
2. Service resolves the `WorkflowSpec` from the registry and opens a provider session handle (per conversation).
3. The user message is appended to the conversation log; a recorder entry is opened.
4. `InteractionContextBuilder` produces `runtime_ctx` for prompt metadata (location, user, tenant, agent keys).
5. `WorkflowRunner` iterates resolved stages:
   - For each step, optional guard skips it; optional input mapper rewrites input.
   - Calls `provider.runtime.run(...)` with metadata (`workflow_key`, `workflow_run_id`, `stage_name`, etc.).
   - Captures chosen output (structured → text → final), validates against `step.output_schema`, and records step.
   - For parallel stages, branches run via `asyncio.gather`; a reducer combines outputs for the next stage.
6. Final output is validated against `workflow.output_schema`, the run is marked succeeded/cancelled/failed, and a `WorkflowRunResult` is returned.

Streaming flow
--------------
`run_workflow_stream` uses `provider.runtime.run_stream(...)` per step. Stream handlers attach workflow/stage/step metadata to every `AgentStreamEvent`, accumulate the last text/structured output, validate it, and emit lifecycle records. Parallel streaming branches enqueue SSE events as they arrive, then apply the reducer once all branches complete.

Hooks and schemas
-----------------
- Guards: `(current_input, prior_steps) -> bool`
- Input mappers: `(current_input, prior_steps) -> Any`
- Reducers (parallel only): `(outputs, prior_steps) -> Any`
All hooks may be async. Schema validation uses `validate_against_schema` for both step and final outputs; schemas can be pydantic models, Python types wrapped by `AgentOutputSchema`, or raw JSON schema dicts. See `app/workflows/CREATING_WORKFLOWS.md` for authoring guidance.

Sessions, events, and cancellations
-----------------------------------
- Provider session handle is built per conversation; deltas are projected to the conversation event log via `EventProjector` (tool outputs, session items).
- Cancellation is cooperative: `WorkflowService.cancel_run` flags the runner and asks the repository to mark running steps and runs as cancelled.
- Run/step persistence is optional: if no repository is wired, recorder is a no-op.

Programmatic use
----------------
```python
from app.services.workflows.service import build_workflow_service, WorkflowRunRequest
from app.services.agents.context import ConversationActorContext

workflow_service = build_workflow_service(run_repository=...)  # wire repos/services as needed
actor = ConversationActorContext(user_id="u1", tenant_id="t1")

result = await workflow_service.run_workflow(
    "analysis_code",
    request=WorkflowRunRequest(message="Analyze this repo"),
    actor=actor,
)
print(result.final_output)
```

Related docs
------------
- Authoring workflows: `app/workflows/CREATING_WORKFLOWS.md`
- Example specs: `app/workflows/*/spec.py`
