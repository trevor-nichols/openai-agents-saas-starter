"""Helpers for workflow output typing and validation."""

from __future__ import annotations

from typing import Any

import jsonschema
from agents.agent_output import AgentOutputSchema, AgentOutputSchemaBase

SchemaLike = AgentOutputSchemaBase | dict[str, Any] | type[Any] | None


def schema_to_json_schema(schema: SchemaLike) -> dict[str, Any] | None:
    """Normalize a workflow/step output schema to a JSON Schema dict.

    Accepts:
    - An `AgentOutputSchemaBase` (or subclass) instance
    - A Python type (wrapped via `AgentOutputSchema`)
    - A raw JSON schema dict
    - None (returns None)
    """

    if schema is None:
        return None
    if isinstance(schema, dict):
        return schema
    if isinstance(schema, AgentOutputSchemaBase):
        return schema.json_schema()
    if isinstance(schema, type):
        return AgentOutputSchema(schema).json_schema()
    raise TypeError(
        "output_schema must be a dict, AgentOutputSchemaBase, Python type, or None"
    )


def validate_against_schema(
    schema: SchemaLike, value: Any, *, label: str | None = None
) -> Any:
    """Validate ``value`` against the given schema if provided.

    Returns the original value for convenience. Raises ``ValueError`` when the
    payload does not satisfy the schema.
    """

    schema_dict = schema_to_json_schema(schema)
    if schema_dict is None or value is None:
        return value

    try:
        jsonschema.validate(instance=value, schema=schema_dict)
    except jsonschema.ValidationError as exc:  # pragma: no cover - thin wrapper
        label_txt = label or "output"
        raise ValueError(f"{label_txt} does not match declared schema: {exc.message}") from exc
    return value


__all__ = ["SchemaLike", "schema_to_json_schema", "validate_against_schema"]
