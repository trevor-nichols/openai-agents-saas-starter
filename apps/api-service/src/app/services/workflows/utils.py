"""Pure helpers for workflow orchestration."""

from __future__ import annotations

from app.workflows._shared.specs import WorkflowSpec


def first_agent_key(workflow: WorkflowSpec) -> str | None:
    for stage in workflow.resolved_stages():
        for step in stage.steps:
            return step.agent_key
    return None


def workflow_agent_keys(workflow: WorkflowSpec) -> list[str]:
    seen: set[str] = set()
    for stage in workflow.resolved_stages():
        for step in stage.steps:
            seen.add(step.agent_key)
    return list(seen)


__all__ = ["first_agent_key", "workflow_agent_keys"]
