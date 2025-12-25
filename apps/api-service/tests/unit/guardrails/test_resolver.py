"""Tests for GuardrailResolver behavior."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from app.guardrails._shared.registry import GuardrailRegistry
from app.guardrails._shared.resolver import GuardrailResolver
from app.guardrails._shared.specs import (
    AgentGuardrailConfig,
    GuardrailCheckConfig,
    GuardrailCheckResult,
    GuardrailSpec,
)


class RequiredConfig(BaseModel):
    threshold: float


async def dummy_check(
    content: str,
    config: dict[str, Any],
    conversation_history: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
) -> GuardrailCheckResult:
    return GuardrailCheckResult(tripwire_triggered=False, info={"content": content})


def _registry() -> GuardrailRegistry:
    reg = GuardrailRegistry()
    reg.register_spec(
        GuardrailSpec(
            key="required_config_guard",
            display_name="Required Config Guard",
            description="Guardrail with required config",
            stage="input",
            engine="regex",
            config_schema=RequiredConfig,
            check_fn_path="tests.unit.guardrails.test_resolver:dummy_check",
        )
    )
    return reg


def test_resolver_validates_config_on_resolve() -> None:
    registry = _registry()
    resolver = GuardrailResolver(registry)
    config = AgentGuardrailConfig(guardrail_keys=("required_config_guard",))

    with pytest.raises(ValidationError):
        resolver.resolve(config)


def test_resolver_accepts_explicit_config() -> None:
    registry = _registry()
    resolver = GuardrailResolver(registry)
    config = AgentGuardrailConfig(
        guardrails=(
            GuardrailCheckConfig(
                guardrail_key="required_config_guard",
                config={"threshold": 0.7},
            ),
        )
    )

    resolved = resolver.resolve(config)
    assert resolved[0].config_dict()["threshold"] == 0.7
