# Workflow Orchestration

We model deterministic flows over OpenAI Agents via `WorkflowSpec`. A spec can be:
- **Single-stage (classic)**: provide `steps` and we wrap them in one sequential stage.
- **Multi-stage**: provide `stages`, each with a `mode` (`sequential` or `parallel`). Parallel stages fan out across steps and optionally use a `reducer` callable to consolidate outputs before the next stage.

Key primitives:
- `WorkflowStep`: agent key, optional `guard`, `input_mapper`, and per-step `max_turns`.
- `WorkflowStage`: name, mode, steps, optional `reducer` (dotted path `outputs, prior_steps -> next_input`).
- `WorkflowSpec`: declarative container; `step_count` sums steps across stages.

## Relationship to agents
- Workflows reference existing agents by `agent_key`; they do not redefine prompts, tools, guardrails, models, or memory. All of that comes from the underlying `AgentSpec`.
- Agent-level guardrails, tool guardrails, and memory defaults still apply when a workflow step invokes that agent.
- Use `input_mapper` to shape what each step receives; use stage `reducer` to merge parallel outputs; use step or workflow `output_schema` to validate structured outputs.
- If you need a new capability, add it to the agent spec (prompt/tools/guardrails) first, then reference that agent in the workflow.

## Guards & input mappers
- `guard`: dotted callable `(current_input, prior_steps) -> bool`; when False, the step is skipped.
- `input_mapper`: dotted callable `(current_input, prior_steps) -> str | dict | list`; return value becomes the next step’s input message/content.
- Both are looked up by dotted path; keep them in module-level functions for importability and reuse.
- `prior_steps` is a list of `WorkflowStepResult` objects; for parallel stages it includes the branch results, for sequential it contains prior step results in order.

## Authoring checklist
- [ ] Define `WorkflowSpec` in `app/workflows/<key>/spec.py` with `key`, `display_name`, `description`.
- [ ] Choose `steps` (single stage) or `stages` with explicit `mode` and optional `reducer` for parallel fan-in.
- [ ] Confirm every `agent_key` exists (and is loaded) in agent specs; add capabilities to the agent spec if needed.
- [ ] Add `guard` / `input_mapper` dotted paths if conditional logic or reshaping is required.
- [ ] Add step-level `output_schema` or workflow `output_schema` if you need validation.
- [ ] Set `allow_handoff_agents=True` only if you expect agents in the workflow to perform handoffs.
- [ ] Add tests if the workflow is business-critical; reuse shared guards/mappers where possible.

Runtime behavior (see `services/workflows/runner.py`):
- Entire workflow runs inside `agents.trace` for unified observability.
- Sequential stages behave like the prior implementation.
- Parallel stages use `asyncio.gather` (sync) or multiplexed streams (streaming) and tag results with `stage_name`, `parallel_group`, `branch_index`.
- Memory strategies: Workflows do **not** declare memory settings. Each step inherits the agent's resolved memory configuration (request → conversation → agent spec defaults). If a step calls an agent with trim/summarize/compact enabled, that run uses the strategy automatically; other agents in the same workflow keep their own defaults. Prompt summaries are injected per agent run when enabled; there is no cross-agent handoff-based summarizer.

Example (fan-out + synthesis):

```python
from app.workflows._shared.specs import WorkflowSpec, WorkflowStage, WorkflowStep

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
                WorkflowStep(agent_key="researcher"),
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
