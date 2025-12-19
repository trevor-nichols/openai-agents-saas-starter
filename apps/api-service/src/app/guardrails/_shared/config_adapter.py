"""Adapter to load Guardrails config bundles and map to internal configs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, ValidationError

from app.agents._shared.specs import GuardrailRuntimeOptions
from app.guardrails._shared.registry import GuardrailRegistry
from app.guardrails._shared.specs import (
    AgentGuardrailConfig,
    GuardrailCheckConfig,
    ToolGuardrailConfig,
)


class GuardrailConfigError(Exception):
    """Raised when guardrail bundle parsing or resolution fails."""


class JsonString(BaseModel):
    """Explicit wrapper to treat a string as JSON content."""

    content: str


class GuardrailConfig(BaseModel):
    """Single guardrail config entry."""

    name: str = Field(..., description="Registered guardrail key")
    config: dict[str, Any] = Field(default_factory=dict)


class BundleConfig(BaseModel):
    """Execution-level bundle config."""

    concurrency: int | None = Field(default=None, ge=1)
    suppress_tripwire: bool = False


class ConfigBundle(BaseModel):
    """Bundle of guardrail configs for a stage."""

    version: int = 1
    guardrails: list[GuardrailConfig]
    config: BundleConfig | None = None


class PipelineBundles(BaseModel):
    """Pipeline stages for guardrails."""

    version: int = 1
    pre_flight: ConfigBundle | None = None
    input: ConfigBundle | None = None
    output: ConfigBundle | None = None
    tool_input: ConfigBundle | None = None
    tool_output: ConfigBundle | None = None

    def stages(self) -> dict[str, ConfigBundle]:
        return {
            key: bundle
            for key, bundle in {
                "pre_flight": self.pre_flight,
                "input": self.input,
                "output": self.output,
                "tool_input": self.tool_input,
                "tool_output": self.tool_output,
            }.items()
            if bundle is not None
        }


ConfigSource = PipelineBundles | Path | str | dict[str, Any] | JsonString


@dataclass(frozen=True, slots=True)
class ResolvedGuardrailConfig:
    """Resolved configuration ready to attach to agents/tools."""

    agent_guardrails: AgentGuardrailConfig | None
    tool_guardrails: ToolGuardrailConfig | None
    runtime_options: GuardrailRuntimeOptions | None
    stages: tuple[str, ...]


def load_pipeline_bundles(source: ConfigSource) -> PipelineBundles:
    """Load PipelineBundles from path/dict/JSON/model."""

    try:
        if isinstance(source, PipelineBundles):
            return source
        if isinstance(source, JsonString):
            data = json.loads(source.content)
            return PipelineBundles.model_validate(data)
        if isinstance(source, (str, Path)):  # noqa: UP038 - tuple required for isinstance
            path = Path(source)
            if not path.exists():
                raise GuardrailConfigError(f"Config file not found: {path}")
            data = json.loads(path.read_text())
            return PipelineBundles.model_validate(data)
        if isinstance(source, dict):
            return PipelineBundles.model_validate(source)
    except ValidationError as exc:
        raise GuardrailConfigError(f"Invalid guardrail config: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise GuardrailConfigError(f"Invalid guardrail JSON: {exc}") from exc

    raise GuardrailConfigError("Unsupported guardrail config source type")


def resolve_guardrail_configs(
    pipeline: PipelineBundles, registry: GuardrailRegistry
) -> ResolvedGuardrailConfig:
    """Map pipeline bundles to AgentGuardrailConfig/ToolGuardrailConfig."""

    agent_checks: list[GuardrailCheckConfig] = []
    tool_input_checks: list[GuardrailCheckConfig] = []
    tool_output_checks: list[GuardrailCheckConfig] = []
    stages: list[str] = []
    agent_suppress_flags: list[bool] = []
    tool_input_suppress_flags: list[bool] = []
    tool_output_suppress_flags: list[bool] = []
    concurrency_values: list[int] = []

    for stage, bundle in pipeline.stages().items():
        stages.append(stage)
        suppress_value = bool(bundle.config.suppress_tripwire) if bundle.config else False
        if bundle.config and bundle.config.concurrency is not None:
            concurrency_values.append(bundle.config.concurrency)
        checks = _bundle_to_guardrail_checks(
            bundle,
            registry,
            cast(Literal["pre_flight", "input", "output", "tool_input", "tool_output"], stage),
        )

        if stage in ("pre_flight", "input", "output"):
            agent_checks.extend(checks)
            agent_suppress_flags.append(suppress_value)
        elif stage == "tool_input":
            tool_input_checks.extend(checks)
            tool_input_suppress_flags.append(suppress_value)
        elif stage == "tool_output":
            tool_output_checks.extend(checks)
            tool_output_suppress_flags.append(suppress_value)

    agent_guardrails = (
        AgentGuardrailConfig(
            guardrails=tuple(agent_checks),
            suppress_tripwire=any(agent_suppress_flags),
        )
        if agent_checks
        else None
    )

    tool_guardrails: ToolGuardrailConfig | None = None
    if tool_input_checks or tool_output_checks:
        tool_guardrails = ToolGuardrailConfig(
            input=AgentGuardrailConfig(
                guardrails=tuple(tool_input_checks),
                suppress_tripwire=any(tool_input_suppress_flags),
            )
            if tool_input_checks
            else None,
            output=AgentGuardrailConfig(
                guardrails=tuple(tool_output_checks),
                suppress_tripwire=any(tool_output_suppress_flags),
            )
            if tool_output_checks
            else None,
            enabled=True,
        )

    runtime_options: GuardrailRuntimeOptions | None = None
    if concurrency_values:
        runtime_options = GuardrailRuntimeOptions(concurrency=min(concurrency_values))

    return ResolvedGuardrailConfig(
        agent_guardrails=agent_guardrails,
        tool_guardrails=tool_guardrails,
        runtime_options=runtime_options,
        stages=tuple(stages),
    )


def _bundle_to_guardrail_checks(
    bundle: ConfigBundle,
    registry: GuardrailRegistry,
    stage: Literal["pre_flight", "input", "output", "tool_input", "tool_output"],
) -> list[GuardrailCheckConfig]:
    checks: list[GuardrailCheckConfig] = []
    unknown: list[str] = []
    stage_mismatch: list[str] = []

    for entry in bundle.guardrails:
        spec = registry.get_spec(entry.name)
        if spec is None:
            unknown.append(entry.name)
            continue
        if spec.stage != stage:
            stage_mismatch.append(f"{entry.name} (expected {stage}, found {spec.stage})")
            continue
        checks.append(
            GuardrailCheckConfig(
                guardrail_key=entry.name,
                config=entry.config,
                enabled=True,
            )
        )

    if unknown:
        raise GuardrailConfigError(f"Unknown guardrail(s): {', '.join(unknown)}")
    if stage_mismatch:
        raise GuardrailConfigError(f"Stage mismatch: {', '.join(stage_mismatch)}")

    return checks


__all__ = [
    "ConfigSource",
    "GuardrailConfigError",
    "PipelineBundles",
    "ConfigBundle",
    "JsonString",
    "ResolvedGuardrailConfig",
    "load_pipeline_bundles",
    "resolve_guardrail_configs",
]
