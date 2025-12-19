# Guardrail specification and model resolution.

This module defines the `GuardrailSpec` dataclass, which captures the metadata, configuration schema, and logic for a guardrail. It also includes a structured metadata model for attaching descriptive and extensible information to guardrails, and instantiation logic for producing executable guardrail instances.

## `GuardrailSpecMetadata`
**Bases:** `BaseModel`

Structured metadata for a guardrail specification.

This model provides an extensible, strongly-typed way to attach metadata to guardrails for discovery, documentation, or engine-specific introspection.

### Attributes:

| Name | Type | Description |
| :--- | :--- | :--- |
| `engine` | `str` \| `None` | Short string identifying the implementation type or engine backing the guardrail (e.g., "regex", "LLM", "API"). Optional. |
| `uses_conversation_history` | `bool` | Whether the guardrail analyzes conversation history in addition to the current input. Defaults to `False`. |

*Source code in `src/guardrails/spec.py`*

---

## `GuardrailSpec` dataclass
**Bases:** `Generic[TContext, TIn, TCfg]`

Immutable descriptor for a registered guardrail.

Encapsulates all static information about a guardrail, including its name, human description, supported media type, configuration schema, the validation function, context requirements, and optional metadata.

`GuardrailSpec` instances are registered for cataloguing and introspection, but should be instantiated with user configuration to create a runnable guardrail for actual use.

### Attributes:

| Name | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Unique registry key for the guardrail. |
| `description` | `str` | Human-readable explanation of the guardrail's purpose. |
| `media_type` | `str` | MIME type to which the guardrail applies (e.g., "text/plain"). |
| `config_schema` | `type[TCfg]` | Pydantic model class describing configuration. |
| `check_fn` | `CheckFn[TContext, TIn, TCfg]` | Function implementing the guardrail's logic. |
| `ctx_requirements` | `type[BaseModel]` | Context model describing dependencies or runtime requirements. |
| `metadata` | `GuardrailSpecMetadata` \| `None` | Optional structured metadata for discovery and documentation. |

*Source code in `src/guardrails/spec.py`*

---

### `schema`

```python
schema() -> dict[str, Any]
```

Return the JSON schema for the guardrail's configuration model.

This method provides the schema needed for UI validation, documentation, or API introspection.

**Returns:**

| Type | Description |
| :--- | :--- |
| `dict[str, Any]` | JSON schema describing the config model fields. |

*Source code in `src/guardrails/spec.py`*

---

### `instantiate`

```python
instantiate(
    *, config: TCfg
) -> ConfiguredGuardrail[TContext, TIn, TCfg]
```

Produce a configured, executable guardrail from this specification.

This is the main entry point for creating guardrail instances that can be run in a validation pipeline. The returned object is fully bound to this definition and the provided configuration.

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `config` | `TCfg` | Validated configuration for this guardrail. | *required* |

**Returns:**

| Type | Description |
| :--- | :--- |
| `ConfiguredGuardrail[TContext, TIn, TCfg]` | Runnable guardrail instance. |

*Source code in `src/guardrails/spec.py`*