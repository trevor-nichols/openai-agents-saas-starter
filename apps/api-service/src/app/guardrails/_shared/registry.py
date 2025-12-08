"""Guardrail registry for managing and discovering guardrail specifications.

This module provides a centralized registry for guardrail specs and presets,
following the same pattern as `app.utils.tools.registry.ToolRegistry`.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from app.guardrails._shared.specs import GuardrailPreset, GuardrailSpec

logger = logging.getLogger(__name__)


class GuardrailRegistry:
    """Inventory of guardrails and presets available to agents.

    This registry maintains:
    - Guardrail specifications (keyed by unique identifier)
    - Guardrail presets (named bundles of guardrail configurations)

    Thread-safe for reads; registration should happen at startup.
    """

    def __init__(self) -> None:
        self._specs: dict[str, GuardrailSpec] = {}
        self._presets: dict[str, GuardrailPreset] = {}
        self._spec_order: list[str] = []  # Preserve registration order

    def register_spec(self, spec: GuardrailSpec) -> None:
        """Register a guardrail specification.

        Args:
            spec: The guardrail specification to register.

        Raises:
            ValueError: If a guardrail with the same key is already registered.
        """
        if spec.key in self._specs:
            raise ValueError(f"Guardrail '{spec.key}' is already registered")
        self._specs[spec.key] = spec
        self._spec_order.append(spec.key)
        logger.debug(
            "Registered guardrail: %s (stage=%s, engine=%s)",
            spec.key,
            spec.stage,
            spec.engine,
        )

    def register_preset(self, preset: GuardrailPreset) -> None:
        """Register a guardrail preset.

        Args:
            preset: The preset to register.

        Raises:
            ValueError: If a preset with the same key is already registered.
            ValueError: If the preset references unknown guardrails.
        """
        if preset.key in self._presets:
            raise ValueError(f"Preset '{preset.key}' is already registered")

        # Validate that all referenced guardrails exist
        unknown = [
            cfg.guardrail_key
            for cfg in preset.guardrails
            if cfg.guardrail_key not in self._specs
        ]
        if unknown:
            raise ValueError(
                f"Preset '{preset.key}' references unknown guardrails: {unknown}"
            )

        self._presets[preset.key] = preset
        logger.debug(
            "Registered preset: %s (%d guardrails)",
            preset.key,
            len(preset.guardrails),
        )

    def get_spec(self, key: str) -> GuardrailSpec | None:
        """Get a guardrail specification by key.

        Args:
            key: The guardrail's unique identifier.

        Returns:
            The spec if found, None otherwise.
        """
        return self._specs.get(key)

    def get_preset(self, key: str) -> GuardrailPreset | None:
        """Get a guardrail preset by key.

        Args:
            key: The preset's unique identifier.

        Returns:
            The preset if found, None otherwise.
        """
        return self._presets.get(key)

    def list_specs(self) -> Sequence[GuardrailSpec]:
        """List all registered guardrail specifications.

        Returns:
            Sequence of specs in registration order.
        """
        return [self._specs[key] for key in self._spec_order]

    def list_presets(self) -> Sequence[GuardrailPreset]:
        """List all registered presets.

        Returns:
            Sequence of presets.
        """
        return list(self._presets.values())

    def list_spec_keys(self) -> list[str]:
        """List all registered guardrail keys.

        Returns:
            List of guardrail keys in registration order.
        """
        return list(self._spec_order)

    def list_preset_keys(self) -> list[str]:
        """List all registered preset keys.

        Returns:
            List of preset keys.
        """
        return list(self._presets.keys())

    def specs_by_stage(self, stage: str) -> list[GuardrailSpec]:
        """Get all guardrail specs for a given stage.

        Args:
            stage: The stage to filter by (pre_flight, input, output, etc.).

        Returns:
            List of specs matching the stage.
        """
        return [spec for spec in self._specs.values() if spec.stage == stage]

    def specs_by_engine(self, engine: str) -> list[GuardrailSpec]:
        """Get all guardrail specs using a given engine.

        Args:
            engine: The engine type to filter by (regex, llm, api, hybrid).

        Returns:
            List of specs matching the engine.
        """
        return [spec for spec in self._specs.values() if spec.engine == engine]

    def clear(self) -> None:
        """Clear all registered specs and presets.

        Primarily for testing purposes.
        """
        self._specs.clear()
        self._presets.clear()
        self._spec_order.clear()

    def __len__(self) -> int:
        """Return the number of registered guardrail specs."""
        return len(self._specs)

    def __contains__(self, key: str) -> bool:
        """Check if a guardrail key is registered."""
        return key in self._specs


@lru_cache
def get_guardrail_registry() -> GuardrailRegistry:
    """Get the singleton guardrail registry.

    Uses LRU cache to ensure a single instance across the application.
    The registry should be initialized at application startup via
    `initialize_guardrails()`.

    Returns:
        The global GuardrailRegistry instance.
    """
    return GuardrailRegistry()


__all__ = [
    "GuardrailRegistry",
    "get_guardrail_registry",
]
