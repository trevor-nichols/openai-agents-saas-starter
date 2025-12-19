"""Guardrail spec and preset discovery and loading.

This module provides functions to discover and load guardrail specifications
from disk, following the same pattern as `app.agents._shared.loaders`.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from app.guardrails._shared.registry import GuardrailRegistry, get_guardrail_registry
from app.guardrails._shared.specs import GuardrailPreset, GuardrailSpec

logger = logging.getLogger(__name__)

# Base paths for guardrail discovery
_CHECKS_DIR = Path(__file__).resolve().parent.parent / "checks"
_PRESETS_DIR = Path(__file__).resolve().parent.parent / "presets"


def load_guardrail_specs(
    checks_dir: Path | None = None,
) -> list[GuardrailSpec]:
    """Discover and load guardrail specifications from disk.

    Scans the checks directory for subdirectories containing a `spec.py`
    module with a `get_guardrail_spec()` function.

    Args:
        checks_dir: Directory to scan for guardrail checks. Defaults to
            `app/guardrails/checks/`.

    Returns:
        List of loaded GuardrailSpec instances.
    """
    base_dir = checks_dir or _CHECKS_DIR
    specs: list[GuardrailSpec] = []

    if not base_dir.exists():
        logger.warning("Guardrails checks directory does not exist: %s", base_dir)
        return specs

    for entry in sorted(base_dir.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("_"):
            continue

        spec_file = entry / "spec.py"
        if not spec_file.exists():
            logger.debug("Skipping %s: no spec.py found", entry.name)
            continue

        try:
            spec = _load_guardrail_spec(entry.name)
            if spec:
                specs.append(spec)
                logger.debug("Loaded guardrail spec: %s", spec.key)
        except Exception:
            logger.exception("Failed to load guardrail spec from %s", entry.name)

    logger.info("Loaded %d guardrail specs", len(specs))
    return specs


def _load_guardrail_spec(check_name: str) -> GuardrailSpec | None:
    """Load a single guardrail spec by check name.

    Args:
        check_name: Directory name of the check (e.g., "pii_detection").

    Returns:
        The loaded GuardrailSpec, or None if loading failed.
    """
    module_path = f"app.guardrails.checks.{check_name}.spec"
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        logger.warning("Could not import %s: %s", module_path, e)
        return None

    factory = getattr(module, "get_guardrail_spec", None)
    if factory is None:
        logger.warning("Module %s has no get_guardrail_spec function", module_path)
        return None

    return factory()


def load_guardrail_presets(
    presets_dir: Path | None = None,
) -> list[GuardrailPreset]:
    """Discover and load guardrail presets from disk.

    Scans the presets directory for Python modules with a `get_preset()`
    function.

    Args:
        presets_dir: Directory to scan for presets. Defaults to
            `app/guardrails/presets/`.

    Returns:
        List of loaded GuardrailPreset instances.
    """
    base_dir = presets_dir or _PRESETS_DIR
    presets: list[GuardrailPreset] = []

    if not base_dir.exists():
        logger.warning("Guardrails presets directory does not exist: %s", base_dir)
        return presets

    for entry in sorted(base_dir.iterdir()):
        if not entry.is_file():
            continue
        if not entry.suffix == ".py":
            continue
        if entry.name.startswith("_"):
            continue

        preset_name = entry.stem
        try:
            preset = _load_guardrail_preset(preset_name)
            if preset:
                presets.append(preset)
                logger.debug("Loaded guardrail preset: %s", preset.key)
        except Exception:
            logger.exception("Failed to load guardrail preset from %s", preset_name)

    logger.info("Loaded %d guardrail presets", len(presets))
    return presets


def _load_guardrail_preset(preset_name: str) -> GuardrailPreset | None:
    """Load a single guardrail preset by name.

    Args:
        preset_name: Module name of the preset (e.g., "standard").

    Returns:
        The loaded GuardrailPreset, or None if loading failed.
    """
    module_path = f"app.guardrails.presets.{preset_name}"
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        logger.warning("Could not import %s: %s", module_path, e)
        return None

    factory = getattr(module, "get_preset", None)
    if factory is None:
        logger.debug("Module %s has no get_preset function", module_path)
        return None

    return factory()


def initialize_guardrails(
    registry: GuardrailRegistry | None = None,
    checks_dir: Path | None = None,
    presets_dir: Path | None = None,
) -> GuardrailRegistry:
    """Initialize the guardrail registry with all discovered specs and presets.

    This function should be called at application startup to populate
    the registry. It:
    1. Loads all guardrail specs from the checks directory
    2. Registers them with the registry
    3. Loads all presets from the presets directory
    4. Registers them with the registry

    Args:
        registry: Registry to populate. Defaults to the singleton.
        checks_dir: Directory to scan for checks.
        presets_dir: Directory to scan for presets.

    Returns:
        The populated GuardrailRegistry.
    """
    reg = registry or get_guardrail_registry()

    # Load and register specs first (presets depend on them)
    specs = load_guardrail_specs(checks_dir)
    for spec in specs:
        if spec.key not in reg:
            reg.register_spec(spec)

    # Load and register presets
    presets = load_guardrail_presets(presets_dir)
    for preset in presets:
        if preset.key not in reg.list_preset_keys():
            try:
                reg.register_preset(preset)
            except ValueError as e:
                # Log but don't fail - preset may reference unimplemented guardrails
                logger.warning("Skipping preset '%s': %s", preset.key, e)

    logger.info(
        "Guardrails initialized: %d specs, %d presets",
        len(reg),
        len(reg.list_preset_keys()),
    )
    return reg


__all__ = [
    "load_guardrail_specs",
    "load_guardrail_presets",
    "initialize_guardrails",
]
