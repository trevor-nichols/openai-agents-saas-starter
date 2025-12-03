from __future__ import annotations

import json
from typing import Any

from app.workflows.specs import WorkflowSpec, WorkflowStage, WorkflowStep


def concat_outputs(outputs: list[Any], prior_steps):
    """Reducer that joins parallel outputs with separators."""

    rendered: list[str] = []
    for out in outputs:
        if out is None:
            continue
        if isinstance(out, str):
            rendered.append(out)
        else:
            try:
                rendered.append(json.dumps(out, ensure_ascii=False))
            except Exception:
                rendered.append(str(out))
    return "\n\n---\n\n".join(rendered)


def passthrough(current_input: Any, _prior_steps):
    return current_input


def get_workflow_spec() -> WorkflowSpec:
    """Parallel fan-out to analysis + code, then synthesize."""

    return WorkflowSpec(
        key="analysis_parallel",
        display_name="Parallel Analysis + Code",
        description=(
            "Fan out to the Data Analyst and Code Assistant in parallel, then"
            " synthesize their outputs into a single response."
        ),
        stages=(
            WorkflowStage(
                name="fanout",
                mode="parallel",
                steps=(
                    WorkflowStep(agent_key="researcher", name="analysis"),
                    WorkflowStep(agent_key="code_assistant", name="code"),
                ),
                reducer="app.workflows.analysis_parallel.spec:concat_outputs",
            ),
            WorkflowStage(
                name="synthesis",
                mode="sequential",
                steps=(
                    WorkflowStep(
                        agent_key="code_assistant",
                        name="synthesis",
                        input_mapper="app.workflows.analysis_parallel.spec:passthrough",
                    ),
                ),
            ),
        ),
        allow_handoff_agents=False,
    )
