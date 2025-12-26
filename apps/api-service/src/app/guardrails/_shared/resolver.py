"""Guardrail resolution and check-function loading.

Resolves GuardrailSpec instances from AgentGuardrailConfig and prepares
validated configs + check functions for execution. This keeps the GuardrailBuilder
focused on orchestration while this module owns config resolution and imports.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from app.guardrails._shared.specs import AgentGuardrailConfig, GuardrailSpec

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from app.guardrails._shared.registry import GuardrailRegistry
    from app.guardrails._shared.specs import GuardrailCheckResult

    CheckFn = Callable[..., Awaitable[GuardrailCheckResult]]


@dataclass(frozen=True, slots=True)
class ResolvedGuardrail:
    """Resolved guardrail ready for runtime execution."""

    spec: GuardrailSpec
    config_model: BaseModel
    check_fn: CheckFn

    def config_dict(self) -> dict[str, Any]:
        """Return a fresh config dict for each invocation."""
        return self.config_model.model_dump()


class GuardrailResolver:
    """Resolves guardrails and loads check functions."""

    def __init__(self, registry: GuardrailRegistry) -> None:
        self._registry = registry
        self._check_fn_cache: dict[str, CheckFn] = {}

    def resolve(self, config: AgentGuardrailConfig) -> list[ResolvedGuardrail]:
        """Resolve guardrails from config and validate their configs."""
        if config.is_empty():
            return []

        resolved = self._resolve_guardrails(config)
        result: list[ResolvedGuardrail] = []
        for spec, raw_config in resolved:
            check_fn = self._get_check_fn(spec)
            validated = spec.validate_config(raw_config)
            result.append(
                ResolvedGuardrail(
                    spec=spec,
                    config_model=validated,
                    check_fn=check_fn,
                )
            )
        return result

    def _resolve_guardrails(
        self,
        config: AgentGuardrailConfig,
    ) -> list[tuple[GuardrailSpec, dict[str, Any]]]:
        """Resolve all guardrails from preset + explicit config."""
        result: dict[str, tuple[GuardrailSpec, dict[str, Any]]] = {}

        # 1. Apply preset first
        if config.preset:
            preset = self._registry.get_preset(config.preset)
            if not preset:
                raise ValueError(f"Guardrail preset '{config.preset}' not found")
            for check_cfg in preset.guardrails:
                if not check_cfg.enabled:
                    continue
                spec = self._registry.get_spec(check_cfg.guardrail_key)
                if spec:
                    merged = {**spec.default_config, **check_cfg.config}
                    result[check_cfg.guardrail_key] = (spec, merged)

        # 2. Apply explicit guardrail keys (with default config)
        for key in config.guardrail_keys:
            spec = self._registry.get_spec(key)
            if not spec:
                raise ValueError(f"Guardrail '{key}' not found in registry")
            if key not in result:
                result[key] = (spec, dict(spec.default_config))

        # 3. Apply explicit guardrail configs (override)
        for check_cfg in config.guardrails:
            spec = self._registry.get_spec(check_cfg.guardrail_key)
            if not spec:
                raise ValueError(
                    f"Guardrail '{check_cfg.guardrail_key}' not found in registry"
                )
            if check_cfg.enabled:
                merged = {**spec.default_config, **check_cfg.config}
                result[check_cfg.guardrail_key] = (spec, merged)
            elif check_cfg.guardrail_key in result:
                # Explicit disable
                del result[check_cfg.guardrail_key]

        return list(result.values())

    def _get_check_fn(self, spec: GuardrailSpec) -> CheckFn:
        """Import and cache the check function."""
        if spec.key not in self._check_fn_cache:
            self._check_fn_cache[spec.key] = self._import_check_fn(spec.check_fn_path)
        return self._check_fn_cache[spec.key]

    @staticmethod
    def _import_check_fn(path: str) -> CheckFn:
        """Import a check function from a dotted path."""
        if ":" in path:
            module_path, attr = path.split(":", 1)
        elif "." in path:
            module_path, attr = path.rsplit(".", 1)
        else:
            raise ValueError(f"Invalid check function path: '{path}'")

        try:
            module = importlib.import_module(module_path)
        except ImportError as exc:
            raise ValueError(f"Could not import module '{module_path}': {exc}") from exc

        fn = getattr(module, attr, None)
        if fn is None:
            raise ValueError(f"Check function '{attr}' not found in '{module_path}'")

        return fn


__all__ = ["GuardrailResolver", "ResolvedGuardrail"]
