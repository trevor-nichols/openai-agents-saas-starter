# Workflow Orchestration

We model deterministic flows over OpenAI Agents via `WorkflowSpec`. A spec can be:
- **Single-stage (classic)**: provide `steps` and we wrap them in one sequential stage.
- **Multi-stage**: provide `stages`, each with a `mode` (`sequential` or `parallel`). Parallel stages fan out across steps and optionally use a `reducer` callable to consolidate outputs before the next stage.

Key primitives:
- `WorkflowStep`: agent key, optional `guard`, `input_mapper`, and per-step `max_turns`.
- `WorkflowStage`: name, mode, steps, optional `reducer` (dotted path `outputs, prior_steps -> next_input`).
- `WorkflowSpec`: declarative container; `step_count` sums steps across stages.

Runtime behavior (see `services/workflows/runner.py`):
- Entire workflow runs inside `agents.trace` for unified observability.
- Sequential stages behave like the prior implementation.
- Parallel stages use `asyncio.gather` (sync) or multiplexed streams (streaming) and tag results with `stage_name`, `parallel_group`, `branch_index`.

Example (fan-out + synthesis):

```python
from app.workflows.specs import WorkflowSpec, WorkflowStage, WorkflowStep

def concat(outputs, _):
    return " | ".join(str(o) for o in outputs if o is not None)

WorkflowSpec(
    key="analysis_parallel",
    display_name="Parallel Analysis + Code",
    description="Fan out then synthesize.",
    stages=(
        WorkflowStage(
            name="fanout",
            mode="parallel",
            steps=(
                WorkflowStep(agent_key="data_analyst"),
                WorkflowStep(agent_key="code_assistant"),
            ),
            reducer="app.workflows.analysis_parallel.spec:concat_outputs",
        ),
        WorkflowStage(
            name="synthesis",
            steps=(WorkflowStep(agent_key="code_assistant"),),
        ),
    ),
)
```

See `app/workflows/analysis_parallel/spec.py` for the full runnable example.
