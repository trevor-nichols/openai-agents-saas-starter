"""Guardrails subsystem for AI agent safety and policy enforcement.

This package provides a declarative, registry-based guardrails system that integrates
with the OpenAI Agents SDK. Guardrails run at various stages of agent execution to
detect and prevent policy violations.

Architecture:
- specs.py: Declarative dataclasses (GuardrailSpec, GuardrailCheckResult, etc.)
- registry.py: Centralized guardrail and preset inventory
- loaders.py: Discover and load guardrail specs from disk
- builder.py: Construct SDK-compatible guardrail functions from specs

Usage:
    from app.guardrails import get_guardrail_registry, initialize_guardrails

    # Initialize at startup
    registry = initialize_guardrails()

    # Use in AgentSpec
    agent_spec = AgentSpec(
        key="my_agent",
        guardrails=AgentGuardrailConfig(preset="standard"),
        ...
    )
"""

from app.guardrails._shared.builder import GuardrailBuilder
from app.guardrails._shared.loaders import (
    initialize_guardrails,
    load_guardrail_presets,
    load_guardrail_specs,
)
from app.guardrails._shared.registry import (
    GuardrailRegistry,
    get_guardrail_registry,
)
from app.guardrails._shared.specs import (
    AgentGuardrailConfig,
    GuardrailCheckConfig,
    GuardrailCheckResult,
    GuardrailEngine,
    GuardrailPreset,
    GuardrailSpec,
    GuardrailStage,
)

__all__ = [
    # Specs
    "GuardrailSpec",
    "GuardrailCheckResult",
    "GuardrailPreset",
    "GuardrailCheckConfig",
    "AgentGuardrailConfig",
    "GuardrailStage",
    "GuardrailEngine",
    # Registry
    "GuardrailRegistry",
    "get_guardrail_registry",
    # Loaders
    "initialize_guardrails",
    "load_guardrail_specs",
    "load_guardrail_presets",
    # Builder
    "GuardrailBuilder",
]
