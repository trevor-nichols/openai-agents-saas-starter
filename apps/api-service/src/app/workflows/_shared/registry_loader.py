"""Discovery utilities for workflow specs on disk."""
from __future__ import annotations

import importlib
from collections.abc import Sequence
from pathlib import Path

from app.workflows._shared.specs import WorkflowSpec

WORKFLOWS_ROOT = Path(__file__).resolve().parent.parent


def discover_workflow_modules(root: Path = WORKFLOWS_ROOT) -> Sequence[tuple[str, str]]:
    modules: list[tuple[str, str]] = []
    for path in sorted(root.iterdir()):
        if not path.is_dir() or path.name.startswith("_"):
            continue
        module_path = f"app.workflows.{path.name}.spec"
        modules.append((path.name, module_path))
    return modules


def load_workflow_specs(root: Path = WORKFLOWS_ROOT) -> list[WorkflowSpec]:
    specs: list[WorkflowSpec] = []
    for key, module_path in discover_workflow_modules(root):
        module = importlib.import_module(module_path)
        factory = getattr(module, "get_workflow_spec", None)
        if factory is None:
            raise ImportError(f"Workflow module {module_path} must expose get_workflow_spec()")
        spec = factory()
        if not isinstance(spec, WorkflowSpec):
            raise TypeError(f"{module_path}.get_workflow_spec() must return WorkflowSpec")
        if spec.key != key:
            raise ValueError(
                f"Workflow spec key '{spec.key}' does not match directory name '{key}'"
            )
        spec.ensure_valid()
        specs.append(spec)
    return specs


__all__ = ["load_workflow_specs", "discover_workflow_modules", "WORKFLOWS_ROOT"]

