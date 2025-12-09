# Creating a New Workflow

Workflows allow you to chain multiple Agents together deterministically. While Agents can handle dynamic handoffs on their own, Workflows are used when you need to enforce a specific sequence of operations (e.g., "Research Topic -> Summarize -> Write Code") or execute Agents in parallel.

## 1. Directory Structure

Workflows are auto-discovered from the `src/app/workflows` directory. To create a new workflow, create a new folder matching your desired workflow key.

**Example:** To create a workflow with the key `my_custom_flow`:

1.  Create directory: `src/app/workflows/my_custom_flow/`
2.  Create file: `src/app/workflows/my_custom_flow/__init__.py` (can be empty)
3.  Create file: `src/app/workflows/my_custom_flow/spec.py` (Required)

## 2. Defining the Specification (`spec.py`)

The `spec.py` file must export a function named `get_workflow_spec()` that returns a `WorkflowSpec` object.

### The Basic Structure

```python
# src/app/workflows/my_custom_flow/spec.py
from __future__ import annotations
from app.workflows._shared.specs import WorkflowSpec, WorkflowStep

def get_workflow_spec() -> WorkflowSpec:
    return WorkflowSpec(
        # MUST match the directory name
        key="my_custom_flow", 
        display_name="My Custom Workflow",
        description="A sequential workflow that researches a topic then writes code.",
        
        # Optional: Set to True to make this the default workflow for the system
        default=False, 
        
        # Define the sequence of agents to call
        steps=(
            WorkflowStep(
                agent_key="researcher", # Must match a key in src/app/agents/
                name="gather_info",     # Optional internal step name
                
                # Optional: Limit execution loop (LLM -> Tool -> LLM) count for this step.
                # If the agent enters an infinite loop, this kills the step.
                max_turns=5,            
            ),
            WorkflowStep(
                agent_key="code_assistant",
                name="generate_script",
            ),
        ),
    )
```

### 💡 Tip: Reusing Agents
If you use the same `agent_key` multiple times (e.g., "Research A" then "Research B"), you **must** provide a unique `name` for each step. This allows Mappers and Reducers to distinguish between them in the execution history.

```python
steps=(
    WorkflowStep(agent_key="researcher", name="research_phase_1"),
    WorkflowStep(agent_key="researcher", name="research_phase_2"),
)
```

## 3. Workflow Modes

### A. Sequential (Default)
Use the `steps` parameter in `WorkflowSpec` for a simple, linear chain. If you only supply `steps`, the system wraps them in a single sequential stage named `stage-1`.

**Data Flow & Precedence:**  
The input for Step 2 is automatically set to the output of Step 1. The system determines "Output" based on this priority order:
1.  **Structured Output:** (If the agent enforced a JSON schema).
2.  **Response Text:** (Standard chat response).
3.  **Final Output:** (Fallback for raw tool outputs if no text was generated).

```python
steps=(
    WorkflowStep(agent_key="agent_a"),
    WorkflowStep(agent_key="agent_b"),
)
```

### B. Parallel (Fan-out / Fan-in)
Use the `stages` parameter with `WorkflowStage`. A stage can run multiple steps in parallel.
*   **Data Flow:** All steps in a parallel stage receive the *same* input (the output of the previous stage).
*   **Reducers:** You must provide a **reducer** to combine the results before moving to the next stage. 
    *   *Note:* If no reducer is provided, the next stage receives a raw Python `list` of outputs (e.g., `["Result A", "Result B"]`). If only one branch runs, that single output is forwarded.

```python
from app.workflows._shared.specs import WorkflowSpec, WorkflowStage, WorkflowStep

def get_workflow_spec() -> WorkflowSpec:
    return WorkflowSpec(
        key="parallel_flow",
        display_name="Parallel Analysis",
        description="Analyzes data using two agents simultaneously.",
        stages=(
            # Stage 1: Run in parallel
            WorkflowStage(
                name="analysis_phase",
                mode="parallel",
                steps=(
                    WorkflowStep(agent_key="researcher"),
                    WorkflowStep(agent_key="code_assistant"),
                ),
                # Dotted path to a reducer function (see Section 4)
                reducer="app.workflows.parallel_flow.spec:concat_reducer", 
            ),
            # Stage 2: Synthesis (Sequential)
            # Input will be the string returned by 'concat_reducer'
            WorkflowStage(
                name="summary_phase",
                mode="sequential",
                steps=(
                    WorkflowStep(agent_key="triage"),
                ),
            ),
        ),
    )
```

## 4. Hooks: Mappers, Reducers, and Guards

You can control data flow and execution logic using hook functions defined in your `spec.py`.

**Async Support:** All hook functions can be defined as standard `def` or `async def`. The runner handles both automatically.

**Import rules:** Dotted paths can be `module:attr` or `module.attr`. The registry imports and validates them at startup; missing or non-callable hooks will fail boot.

### ⚠️ Data Reference: `prior_steps`
All hooks receive a `prior_steps` argument. This is a list of `WorkflowStepResult` objects representing the history of the run so far. 

**Object Structure:**
```python
# The object inside the 'prior_steps' list
class WorkflowStepResult:
    name: str                  # The step name
    agent_key: str             # The agent key used
    stage_name: str | None     # Name of the stage it ran in
    response: AgentRunResult   # The full result object
```

**Common attributes on `step.response` (`AgentRunResult`):**
*   `response.response_text`: (str) The text reply.
*   `response.structured_output`: (dict) Parsed JSON if `output_schema` was used.
*   `response.tool_outputs`: (list) Raw tool results, if the step ended on a tool call.
*   `response.usage`: (object) Token usage statistics.

---

### Input Mappers
Modify the input passing from the previous step (or the user) into the current step.
*   **Signature:** `(current_input: Any, prior_steps: Sequence[WorkflowStepResult]) -> Any`
*   **Type Awareness:** If the previous step returned structured output (via `output_schema`), `current_input` will be a **Dict or Pydantic model**, not a string.

```python
def my_mapper(current_input, prior_steps):
    # Example: Find the output of a specific named step
    research_step = next(s for s in prior_steps if s.name == "gather_info")
    return f"Please summarize this research: {research_step.response.response_text}"

# Usage in spec:
# WorkflowStep(..., input_mapper="app.workflows.my_flow.spec:my_mapper")
```

### Reducers (Parallel Only)
Combine outputs from multiple parallel agents into a single input for the next stage.
*   **Signature:** `(outputs: list[Any], prior_steps: Sequence) -> Any`
*   **Note:** `prior_steps` here includes the results of the parallel steps that just finished.
*   **Skipped Steps:** If a step in a parallel stage is skipped via a Guard, it is excluded from the `outputs` list entirely.

```python
def concat_reducer(outputs: list[Any], prior_steps):
    # Join outputs with a separator. 
    results = [str(o) for o in outputs]
    return "\n---\n".join(results)

# Usage in Stage:
# WorkflowStage(..., reducer="app.workflows.my_flow.spec:concat_reducer")
```

### Guards
Conditional logic to skip a step. If the guard returns `False`, the step is skipped.
*   **Signature:** `(current_input: Any, prior_steps: Sequence) -> bool`

```python
def requires_code_guard(current_input, prior_steps):
    return "python" in str(current_input).lower()

# Usage in Step:
# WorkflowStep(..., guard="app.workflows.my_flow.spec:requires_code_guard")
```

## 5. Structured Output

You can enforce schemas on both the final workflow output and intermediate steps using Pydantic models.

Accepted schema shapes:
* `BaseModel` / Python type (wrapped via `AgentOutputSchema`)
* `AgentOutputSchemaBase` instances
* Raw JSON Schema dicts

### Final Output Validation
Enforce the format of the final response returned to the API client.

```python
from pydantic import BaseModel

class FinalReport(BaseModel):
    summary: str
    citation_count: int

def get_workflow_spec() -> WorkflowSpec:
    return WorkflowSpec(
        key="structured_flow",
        # ...
        output_schema=FinalReport 
    )
```

### Intermediate Step Validation
You can also enforce schemas on individual steps. This ensures that the output of one agent matches the expected input format of the next.

```python
WorkflowStep(
    agent_key="extractor",
    # Validates this specific step's output before passing it to the input mapper
    output_schema=ExtractionSchema 
),
```

## 6. Configuration Checklist

1.  **Agent Keys:** Ensure every `agent_key` used in `WorkflowStep` exists in `src/app/agents/`.
2.  **Key Matching:** The `key` in `WorkflowSpec(key="...")` **MUST** match the folder name in `src/app/workflows/`.
3.  **Dotted Paths:** When referencing mappers/reducers, use the full python path string: `"app.workflows.<folder>.spec:<function_name>"`.
4.  **Strict Validation:** By default, `allow_handoff_agents` is `False`.
    *   **CRITICAL:** If `False`, the API Service will **fail to start** if you try to use an Agent that has `handoff_keys` configured in its `AgentSpec`. This protects deterministic workflows from accidental model-driven handoffs.
    *   If you *must* use a handoff-capable agent, set `allow_handoff_agents=True` in your `WorkflowSpec`.
5.  **Default workflow:** Only one workflow may set `default=True`; multiple defaults fail validation.
6.  **Schema validity:** Workflow and step `output_schema` values are validated at startup. Invalid schemas or non-callable hook paths will block service startup.

## 7. Testing

You can manually test your workflow using the HTTP smoke test structure or by creating a new test file in `tests/manual/`.

**Example HTTP Request (with Location Context):**
```http
POST /api/v1/workflows/my_custom_flow/run
Content-Type: application/json
X-Tenant-Id: <your-tenant-id>

{
  "message": "Find coffee shops near me",
  "conversation_id": "optional-uuid-to-resume-chat",
  "share_location": true,
  "location": {
    "city": "San Francisco",
    "region": "CA",
    "country": "US"
  }
}
```

**Streaming:**
The `run-stream` endpoint emits Server-Sent Events (SSE). Unlike standard chat, workflow events include specific metadata identifying the progress through the DAG:
*   `workflow_key`
*   `stage_name`
*   `step_name`
*   `step_agent`