"""Workflow registry for deterministic chains over agents."""

from __future__ import annotations

import importlib
from collections.abc import Sequence

from app.agents._shared.registry_loader import load_agent_specs
from app.agents._shared.specs import AgentSpec
from app.workflows.registry_loader import load_workflow_specs
from app.workflows.schema_utils import schema_to_json_schema
from app.workflows.specs import WorkflowDescriptor, WorkflowSpec


def _import_callable(path: str, label: str):
    if ":" in path:
        module_path, attr = path.split(":", 1)
    elif "." in path:
        module_path, attr = path.rsplit(".", 1)
    else:
        raise ValueError(f"Invalid dotted path for {label}: {path}")
    module = importlib.import_module(module_path)
    obj = getattr(module, attr, None)
    if obj is None or not callable(obj):
        raise ValueError(f"{label} '{path}' must be a callable")
    return obj


class WorkflowRegistry:
    def __init__(
        self,
        *,
        workflow_specs: Sequence[WorkflowSpec] | None = None,
        agent_specs: Sequence[AgentSpec] | None = None,
    ) -> None:
        self._workflow_specs = (
            list(workflow_specs) if workflow_specs is not None else load_workflow_specs()
        )
        self._agent_specs = {spec.key: spec for spec in (agent_specs or load_agent_specs())}
        self._descriptors: dict[str, WorkflowDescriptor] = {}
        self._validate_and_index()

    def list_descriptors(self) -> Sequence[WorkflowDescriptor]:
        return [self._descriptors[k] for k in sorted(self._descriptors.keys())]

    def get(self, key: str) -> WorkflowSpec | None:
        return next((spec for spec in self._workflow_specs if spec.key == key), None)

    @property
    def default_workflow_key(self) -> str | None:
        defaults = [spec.key for spec in self._workflow_specs if spec.default]
        if not defaults:
            return None
        if len(defaults) > 1:
            raise ValueError(f"Multiple default workflows configured: {', '.join(defaults)}")
        return defaults[0]

    def _validate_and_index(self) -> None:
        seen_keys: set[str] = set()
        for spec in self._workflow_specs:
            if spec.key in seen_keys:
                raise ValueError(f"Duplicate workflow key '{spec.key}'")
            seen_keys.add(spec.key)
            self._validate_steps(spec)
            # Fail fast if schema is malformed
            schema_to_json_schema(spec.output_schema)
            self._descriptors[spec.key] = WorkflowDescriptor(
                key=spec.key,
                display_name=spec.display_name,
                description=spec.description.strip(),
                step_count=spec.step_count,
                default=spec.default,
            )

    def _validate_steps(self, spec: WorkflowSpec) -> None:
        for stage in spec.resolved_stages():
            if stage.mode not in {"sequential", "parallel"}:
                raise ValueError(
                    f"Workflow '{spec.key}' stage '{stage.name}' has invalid mode '{stage.mode}'"
                )
            if stage.reducer:
                _import_callable(stage.reducer, "reducer")
            for step in stage.steps:
                if step.agent_key not in self._agent_specs:
                    raise ValueError(
                        "Workflow '{spec.key}' references agent "
                        f"'{step.agent_key}' which is not configured"
                    )
                if not spec.allow_handoff_agents:
                    agent_spec = self._agent_specs[step.agent_key]
                    if getattr(agent_spec, "handoff_keys", ()):
                        raise ValueError(
                            f"Workflow '{spec.key}' disallows handoff-enabled agent "
                            f"'{step.agent_key}'"
                        )
                if step.guard:
                    _import_callable(step.guard, "guard")
                if step.input_mapper:
                    _import_callable(step.input_mapper, "input_mapper")
                schema_to_json_schema(step.output_schema)


_WORKFLOW_REGISTRY: WorkflowRegistry | None = None


def get_workflow_registry() -> WorkflowRegistry:
    global _WORKFLOW_REGISTRY
    if _WORKFLOW_REGISTRY is None:
        _WORKFLOW_REGISTRY = WorkflowRegistry()
    return _WORKFLOW_REGISTRY


__all__ = ["WorkflowRegistry", "get_workflow_registry"]
