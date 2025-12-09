"""Helpers for exposing agent structured-output schemas to API consumers."""

from __future__ import annotations

import importlib
from typing import Any

from agents.agent_output import AgentOutputSchema, AgentOutputSchemaBase

from app.agents._shared.specs import AgentSpec
from app.workflows._shared.schema_utils import SchemaLike, schema_to_json_schema


def _import_object(path: str, *, label: str | None = None) -> Any:
    """Resolve a dotted path into an imported object."""
    dotted = path
    if ":" in dotted:
        module_path, attr = dotted.split(":", 1)
    elif "." in dotted:
        module_path, attr = dotted.rsplit(".", 1)
    else:
        raise ValueError(f"Invalid dotted path '{dotted}'")

    module = importlib.import_module(module_path)
    obj = getattr(module, attr, None)
    if obj is None:
        raise ValueError(f"{label or 'object'} '{dotted}' could not be resolved")
    return obj


def resolve_output_schema(spec: AgentSpec) -> dict[str, Any] | None:
    """Return the JSON Schema for an agent's structured output, if configured."""
    cfg = getattr(spec, "output", None)
    if cfg is None or cfg.mode == "text":
        return None

    schema_like: SchemaLike
    if cfg.custom_schema_path:
        schema_obj = _import_object(cfg.custom_schema_path, label="custom_schema_path")
        if isinstance(schema_obj, type) and issubclass(schema_obj, AgentOutputSchemaBase):
            schema_obj = schema_obj()
        if not isinstance(schema_obj, AgentOutputSchemaBase):
            raise ValueError(
                "custom_schema_path "
                f"'{cfg.custom_schema_path}' must resolve to AgentOutputSchemaBase"
            )
        schema_like = schema_obj
    else:
        if not cfg.type_path:
            raise ValueError(
                f"Agent '{spec.key}' output.mode=json_schema requires 'type_path' to be set"
            )
        type_obj = _import_object(cfg.type_path, label="type_path")
        schema_like = AgentOutputSchema(type_obj, strict_json_schema=cfg.strict)

    return schema_to_json_schema(schema_like)


__all__ = ["resolve_output_schema"]
