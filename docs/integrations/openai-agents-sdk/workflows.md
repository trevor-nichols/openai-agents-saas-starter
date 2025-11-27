# Workflows (deterministic agent chains)

This layer orchestrates multiple Agents SDK instances in a deterministic sequence. Use it when you want a fixed pipeline with guards (e.g., analysis ➜ code), not dynamic handoffs.

## Concepts
- **WorkflowSpec** (code-defined): lives under `api-service/src/app/workflows/<key>/spec.py`.
- **WorkflowStep:** points to an existing `agent_key`; optional `guard` (dotted callable) and `input_mapper` (dotted callable) to control execution and inputs.
- **WorkflowRegistry:** discovers specs on import, validates agent references, and surfaces descriptors for the API catalog.
- **WorkflowRunner/Service:** executes steps using the default provider runtime, reusing `PromptRuntimeContext` (user/tenant/location/container bindings).

## Authoring a workflow
```python
from app.workflows.specs import WorkflowSpec, WorkflowStep

def passthrough(current_input, prior_steps):
    return (prior_steps[-1].response.response_text or current_input) if prior_steps else current_input

def get_workflow_spec() -> WorkflowSpec:
    return WorkflowSpec(
        key="analysis_code",
        display_name="Analysis then Code",
        description="Run data analyst, then feed its output into the code assistant.",
        steps=(
            WorkflowStep(agent_key="data_analyst", name="analysis"),
            WorkflowStep(
                agent_key="code_assistant",
                name="code",
                input_mapper="app.workflows.analysis_code.spec:passthrough",
            ),
        ),
        allow_handoff_agents=False,
    )
```

Place the file at `app/workflows/analysis_code/spec.py`; the registry auto-discovers it.

## API surface
- `GET /api/v1/workflows` — list catalog entries.
- `POST /api/v1/workflows/{key}/run` — run a workflow; body: `{message, conversation_id?, location?, share_location?}`; response includes `workflow_run_id`.
- `POST /api/v1/workflows/{key}/run-stream` — SSE stream of the same run; events carry `workflow_key`, `workflow_run_id`, `step_name`, `step_agent` plus the standard agent stream fields.

Responses include per-step outputs and the final output. Streaming support can be added later via the same runner hooks.

## When to use
- Deterministic pipelines with explicit gating/branching.
- Operator-authored flows that should not rely on model-driven handoffs.
- Keeping agents single-responsibility while composing them predictably.

## Current persistence behavior
- Workflows remain non-chatty (no conversation history), but workflow runs/steps are recorded in dedicated tables (`workflow_runs`, `workflow_run_steps`) for auditing. If you need full transcripts, wire `WorkflowService` to `ConversationService` separately.

## When to stick with handoffs
- Dynamic routing inside a single agent conversation.
- When ownership transfer between agents (with history) is desired.
