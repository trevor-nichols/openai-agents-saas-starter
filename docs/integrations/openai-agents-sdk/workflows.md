# Workflows (deterministic agent chains)

This layer orchestrates multiple Agents SDK instances in a deterministic sequence. Use it when you want a fixed pipeline with guards (e.g., triage ➜ specialist), not dynamic handoffs.

## Concepts
- **WorkflowSpec** (code-defined): lives under `api-service/src/app/workflows/<key>/spec.py`.
- **WorkflowStep:** points to an existing `agent_key`; optional `guard` (dotted callable) and `input_mapper` (dotted callable) to control execution and inputs.
- **WorkflowRegistry:** discovers specs on import, validates agent references, and surfaces descriptors for the API catalog.
- **WorkflowRunner/Service:** executes steps using the default provider runtime, reusing `PromptRuntimeContext` (user/tenant/location/container bindings).

## Authoring a workflow
```python
from app.workflows.specs import WorkflowSpec, WorkflowStep

def guard_requires_analysis(current_input, prior_steps):
    return "analysis" in (prior_steps[-1].response.response_text or "").lower()

def map_use_last_output(current_input, prior_steps):
    return prior_steps[-1].response.response_text or current_input

def get_workflow_spec() -> WorkflowSpec:
    return WorkflowSpec(
        key="triage_pipeline",
        display_name="Triage Pipeline",
        description="Route via triage, then specialists based on guards.",
        steps=(
            WorkflowStep(agent_key="triage", name="triage"),
            WorkflowStep(
                agent_key="data_analyst",
                guard="my.module:guard_requires_analysis",
                input_mapper="my.module:map_use_last_output",
            ),
        ),
        allow_handoff_agents=True,
    )
```

Place the file at `app/workflows/triage_pipeline/spec.py`; the registry auto-discovers it.

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
