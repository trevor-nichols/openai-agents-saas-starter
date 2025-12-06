from __future__ import annotations

from app.workflows.specs import WorkflowSpec, WorkflowStep


def passthrough(current_input: str, prior_steps):
    """Forward the previous step's response if present; otherwise keep input."""

    if prior_steps:
        last = prior_steps[-1].response.response_text
        if last:
            return last
    return current_input


def get_workflow_spec() -> WorkflowSpec:
    """Deterministic demo pipeline: analysis → code."""

    return WorkflowSpec(
        key="analysis_code",
        display_name="Analysis then Code",
        description=(
            "Run the data analyst first, then feed its output into the code assistant. "
            "Shows a simple deterministic chain without model-driven handoffs."
        ),
        steps=(
            WorkflowStep(
                agent_key="researcher",
                name="analysis",
            ),
            WorkflowStep(
                agent_key="code_assistant",
                name="code",
                input_mapper="app.workflows.analysis_code.spec:passthrough",
            ),
        ),
        default=True,
        allow_handoff_agents=False,
    )
