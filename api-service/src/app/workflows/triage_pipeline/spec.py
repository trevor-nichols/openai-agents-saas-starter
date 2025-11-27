from __future__ import annotations

from app.workflows.specs import WorkflowSpec, WorkflowStep


def needs_analysis(_: str, prior_steps):
    if not prior_steps:
        return False
    triage_output = prior_steps[-1].response.response_text or ""
    return "analysis" in triage_output.lower()


def needs_code(_: str, prior_steps):
    if not prior_steps:
        return False
    triage_output = prior_steps[-1].response.response_text or ""
    return "code" in triage_output.lower()


def passthrough_input(current_input: str, prior_steps):
    if prior_steps:
        last = prior_steps[-1].response.response_text
        if last:
            return last
    return current_input


def get_workflow_spec() -> WorkflowSpec:
    return WorkflowSpec(
        key="triage_pipeline",
        display_name="Triage Pipeline",
        description="Route through triage, then specialists based on simple guards.",
        steps=(
            WorkflowStep(
                agent_key="triage",
                name="triage",
                # allow handoff agent for this workflow
            ),
            WorkflowStep(
                agent_key="data_analyst",
                name="analysis",
                guard="app.workflows.triage_pipeline.spec:needs_analysis",
                input_mapper="app.workflows.triage_pipeline.spec:passthrough_input",
            ),
            WorkflowStep(
                agent_key="code_assistant",
                name="code",
                guard="app.workflows.triage_pipeline.spec:needs_code",
                input_mapper="app.workflows.triage_pipeline.spec:passthrough_input",
            ),
        ),
        default=True,
        allow_handoff_agents=True,
    )

