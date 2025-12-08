"""Guardrail specification primitives for declarative guardrail configuration.

Each guardrail provides a lightweight `GuardrailSpec` that describes its key,
stage, engine type, configuration schema, and check function. The GuardrailBuilder
turns these specs into SDK-compatible guardrail functions.

This module follows the same patterns as `app.agents._shared.specs` for consistency.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel

# Type aliases for guardrail configuration
GuardrailStage = Literal["pre_flight", "input", "output", "tool_input", "tool_output"]
"""Stage at which the guardrail runs in the agent execution pipeline."""

GuardrailEngine = Literal["regex", "llm", "api", "hybrid"]
"""Implementation engine backing the guardrail check."""


@dataclass(frozen=True, slots=True)
class GuardrailSpec:
    """Declarative description of a guardrail check.

    Similar to `AgentSpec`, this immutable dataclass captures all metadata
    needed to instantiate and run a guardrail. Guardrail implementations
    provide a `get_guardrail_spec()` function that returns their spec.

    Attributes:
        key: Unique identifier used in configs and lookups (e.g., "pii_detection").
        display_name: Human-friendly label for UI/catalogs (e.g., "PII Detection").
        description: Explanation of what the guardrail detects/enforces.
        stage: When the guardrail runs (pre_flight, input, output, tool_*).
        engine: Implementation type (regex, llm, api, hybrid).
        config_schema: Pydantic model for validating guardrail configuration.
        check_fn_path: Dotted path to the async check function.
        uses_conversation_history: Whether multi-turn context is analyzed.
        default_config: Sensible defaults when config is omitted.
        supports_masking: For PII - can mask content instead of blocking.
        tripwire_on_error: Whether to trigger tripwire if check raises an error.
    """

    key: str
    display_name: str
    description: str
    stage: GuardrailStage
    engine: GuardrailEngine
    config_schema: type[BaseModel]
    check_fn_path: str
    uses_conversation_history: bool = False
    default_config: dict[str, Any] = field(default_factory=dict)
    supports_masking: bool = False
    tripwire_on_error: bool = False

    def validate_config(self, config: dict[str, Any]) -> BaseModel:
        """Validate configuration against the schema.

        Args:
            config: Raw configuration dictionary.

        Returns:
            Validated Pydantic model instance.

        Raises:
            ValidationError: If config doesn't match schema.
        """
        merged = {**self.default_config, **config}
        return self.config_schema(**merged)


@dataclass(frozen=True, slots=True)
class GuardrailCheckResult:
    """Result of a guardrail check execution.

    Returned by check functions to indicate whether a tripwire was triggered
    and provide diagnostic information.

    Attributes:
        tripwire_triggered: Whether the guardrail detected a violation.
        info: Guardrail-specific diagnostic information.
        masked_content: For masking mode, the content with violations masked.
        confidence: For LLM-based checks, the confidence score (0.0-1.0).
        token_usage: Token usage from LLM-based checks (input, output, total).
        execution_failed: True when the guardrail execution raised.
        original_exception: Captures the original exception when available.
    """

    tripwire_triggered: bool
    info: dict[str, Any]
    masked_content: str | None = None
    confidence: float | None = None
    token_usage: dict[str, int] | None = None
    execution_failed: bool = False
    original_exception: Exception | None = None
    stage: str | None = None

    def to_output_info(self) -> dict[str, Any]:
        """Convert to the format expected by SDK guardrail output."""
        result = dict(self.info)
        if self.stage:
            result.setdefault("stage", self.stage)
        if self.confidence is not None:
            result["confidence"] = self.confidence
        if self.masked_content is not None:
            result["masked_content"] = self.masked_content
        if self.token_usage:
            result["token_usage"] = self.token_usage
        if self.execution_failed:
            result["execution_failed"] = True
        if self.original_exception:
            result["error"] = str(self.original_exception)
        return result


@dataclass(frozen=True, slots=True)
class GuardrailCheckConfig:
    """Configuration for a single guardrail instance.

    Used within presets and agent configurations to specify which guardrails
    to enable and their settings.

    Attributes:
        guardrail_key: Registry key of the guardrail to enable.
        config: Configuration overrides for this guardrail.
        enabled: Whether this guardrail is active (allows disabling in overrides).
    """

    guardrail_key: str
    config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class GuardrailPreset:
    """A named collection of guardrail configurations.

    Presets allow operators to apply standard guardrail bundles without
    specifying each guardrail individually. Similar to how theme presets
    work in UI libraries.

    Attributes:
        key: Unique identifier for the preset (e.g., "standard", "strict").
        display_name: Human-friendly label.
        description: Explanation of the preset's purpose and contents.
        guardrails: Ordered tuple of guardrail configurations.
    """

    key: str
    display_name: str
    description: str
    guardrails: tuple[GuardrailCheckConfig, ...]

    def guardrail_keys(self) -> list[str]:
        """Return list of enabled guardrail keys in this preset."""
        return [g.guardrail_key for g in self.guardrails if g.enabled]


@dataclass(frozen=True, slots=True)
class AgentGuardrailConfig:
    """Guardrail configuration for an agent spec.

    Supports three configuration modes that can be combined:

    1. `preset`: Apply a named preset (e.g., "standard", "strict")
    2. `guardrail_keys`: Explicit list of guardrail keys with default config
    3. `guardrails`: Fine-grained per-guardrail configuration

    Resolution order: preset is applied first, then explicit keys/configs override.

    Attributes:
        preset: Named preset to apply (e.g., "standard", "strict", "minimal").
        guardrail_keys: Explicit guardrail keys to enable with default config.
        guardrails: Fine-grained per-guardrail configuration overrides.
        suppress_tripwire: If True, return results instead of raising exceptions.
    """

    preset: str | None = None
    guardrail_keys: tuple[str, ...] = ()
    guardrails: tuple[GuardrailCheckConfig, ...] = ()
    suppress_tripwire: bool = False

    def is_empty(self) -> bool:
        """Check if no guardrails are configured."""
        return self.preset is None and not self.guardrail_keys and not self.guardrails


@dataclass(frozen=True, slots=True)
class ToolGuardrailConfig:
    """Guardrail configuration for a single tool (input/output stages).

    - `input`: Guardrails to run on tool input (tool_input stage).
    - `output`: Guardrails to run on tool output (tool_output stage).
    - `enabled`: Allows disabling guardrails for a specific tool (overrides global).
    """

    input: AgentGuardrailConfig | None = None
    output: AgentGuardrailConfig | None = None
    enabled: bool = True

    def is_empty(self) -> bool:
        if not self.enabled:
            return True
        input_empty = self.input is None or self.input.is_empty()
        output_empty = self.output is None or self.output.is_empty()
        return input_empty and output_empty


def total_guardrail_token_usage(
    results: Iterable[GuardrailCheckResult | None],
) -> dict[str, int | None]:
    """Aggregate token usage across guardrail results.

    Args:
        results: Iterable of guardrail results (can include None).

    Returns:
        Dictionary with aggregated token usage. If no usage is present, all values are None.
    """
    totals: dict[str, int | None] = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    found_usage = False

    for result in results:
        if not result or not result.token_usage:
            continue
        found_usage = True
        tu = result.token_usage
        prompt = tu.get("prompt_tokens", tu.get("input_tokens"))
        completion = tu.get("completion_tokens", tu.get("output_tokens"))
        total = tu.get("total_tokens", tu.get("total"))

        if prompt is not None:
            totals["prompt_tokens"] = (totals["prompt_tokens"] or 0) + prompt
        if completion is not None:
            totals["completion_tokens"] = (totals["completion_tokens"] or 0) + completion
        if total is not None:
            totals["total_tokens"] = (totals["total_tokens"] or 0) + total

    if not found_usage:
        return {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        }

    return totals


# Type alias for the check function signature
# CheckFn = Callable[[str, dict[str, Any], ...], Awaitable[GuardrailCheckResult]]


__all__ = [
    "GuardrailStage",
    "GuardrailEngine",
    "GuardrailSpec",
    "GuardrailCheckResult",
    "GuardrailCheckConfig",
    "GuardrailPreset",
    "AgentGuardrailConfig",
    "ToolGuardrailConfig",
    "total_guardrail_token_usage",
]
