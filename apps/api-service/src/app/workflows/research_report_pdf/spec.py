from __future__ import annotations

from app.workflows._shared.specs import WorkflowSpec, WorkflowStep


def to_pdf_prompt(current_input: str, prior_steps):
    """Shape researcher output into instructions for the PDF designer."""

    research_output = current_input
    if prior_steps:
        last = prior_steps[-1].response
        research_output = (
            last.structured_output
            or last.response_text
            or last.final_output
            or research_output
        )

    return (
        "Using the research below, produce a well-structured PDF report with an executive "
        "summary, key findings, recommendations, and citations.\n\n"
        f"Research:\n{research_output}"
    )


def get_workflow_spec() -> WorkflowSpec:
    return WorkflowSpec(
        key="research_report_pdf",
        display_name="Research to PDF Report",
        description=(
            "Runs the researcher to gather findings, then hands the output to the PDF designer "
            "to produce a polished report."
        ),
        steps=(
            WorkflowStep(
                agent_key="researcher",
                name="research",
            ),
            WorkflowStep(
                agent_key="pdf_designer",
                name="pdf_report",
                input_mapper="app.workflows.research_report_pdf.spec:to_pdf_prompt",
            ),
        ),
        allow_handoff_agents=False,
    )
