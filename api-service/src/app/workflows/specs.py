from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

GuardType = Literal["function"]
InputMapperType = Literal["function"]


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    """One step in a workflow.

    - agent_key: existing Agent key to invoke
    - name: optional friendly name (defaults to agent_key)
    - guard: dotted-path callable returning bool; skips step when False
    - input_mapper: dotted-path callable to produce the next input from prior output + request
    - max_turns: optional override of RunOptions.max_turns per step
    """

    agent_key: str
    name: str | None = None
    guard: str | None = None
    guard_type: GuardType | None = "function"
    input_mapper: str | None = None
    input_mapper_type: InputMapperType | None = "function"
    max_turns: int | None = None

    def display_name(self) -> str:
        return self.name or self.agent_key


@dataclass(frozen=True, slots=True)
class WorkflowStage:
    """A stage groups one or more steps and defines how they execute.

    - name: friendly label for observability/DB
    - mode: "sequential" (default) or "parallel"
    - steps: ordered steps inside the stage
    - reducer: dotted-path callable to consolidate parallel results into the
      next stage's input; if omitted for parallel, defaults to list of outputs.
    """

    name: str
    steps: Sequence[WorkflowStep]
    mode: Literal["sequential", "parallel"] = "sequential"
    reducer: str | None = None

    def ensure_valid(self) -> None:
        if not self.steps:
            raise ValueError(f"Stage '{self.name}' must include at least one step")


@dataclass(frozen=True, slots=True)
class WorkflowSpec:
    """Declarative description of a deterministic workflow over agents."""

    key: str
    display_name: str
    description: str
    steps: Sequence[WorkflowStep] | None = None
    stages: Sequence[WorkflowStage] | None = None
    default: bool = False
    allow_handoff_agents: bool = False  # optional guardrail for strict chains

    def ensure_valid(self) -> None:
        resolved = self.resolved_stages()
        if not resolved:
            raise ValueError(f"Workflow '{self.key}' must define at least one stage/step")
        for stage in resolved:
            stage.ensure_valid()

    def resolved_stages(self) -> list[WorkflowStage]:
        """Return explicit stages, synthesizing one when only steps are provided."""

        if self.stages and len(self.stages) > 0:
            return list(self.stages)
        # Backward compatibility: wrap flat steps in a single sequential stage.
        return [WorkflowStage(name="stage-1", steps=self.steps or (), mode="sequential")]

    @property
    def step_count(self) -> int:
        return sum(len(stage.steps) for stage in self.resolved_stages())


@dataclass(frozen=True, slots=True)
class WorkflowDescriptor:
    key: str
    display_name: str
    description: str
    step_count: int
    default: bool
