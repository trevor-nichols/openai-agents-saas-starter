# Registry

Registry for managing `GuardrailSpec` instances and maintaining a catalog of guardrails.

This module provides the in-memory registry that acts as the authoritative catalog for all available guardrail specifications. The registry supports registration, lookup, removal, and metadata inspection for guardrails, enabling extensibility and dynamic discovery across your application.

---

### `default_spec_registry` module-attribute

```python
default_spec_registry = GuardrailRegistry()
```

Global default registry for guardrail specifications.

This instance should be used for registration and lookup unless a custom registry is explicitly required.

---

### `Metadata` dataclass

Metadata snapshot for a guardrail specification.

This container bundles descriptive and structural details about a guardrail for inspection, discovery, or documentation.

**Attributes:**

| Name | Type | Description |
| :--- | :--- | :--- |
| **`name`** | `str` | Unique identifier for the guardrail. |
| **`description`** | `str` | Explanation of what the guardrail checks. |
| **`media_type`** | `str` | MIME type (e.g. "text/plain") the guardrail applies to. |
| **`config_schema`** | `dict[str, Any]` \| `None` | JSON schema for the guardrail's config model. |
| **`metadata`** | `dict[str, Any]` \| `None` | Additional metadata (e.g., engine type). |

*Source code in `src/guardrails/registry.py`*

---

## `GuardrailRegistry`

Central registry for all registered guardrail specifications.

This class provides methods to register, remove, and look up `:class:GuardrailSpec` objects by name. It supports dynamic extension of available guardrails and powers discovery and validation throughout the package.

**Typical usage**

```python
registry = GuardrailRegistry()
registry.register(...)
spec = registry.get("my_guardrail")
all_specs = registry.get_all()
```

*Source code in `src/guardrails/registry.py`*

---

### `__init__`

```python
__init__() -> None
```

Initialize an empty registry of guardrail specifications.

*Source code in `src/guardrails/registry.py`*

---

### `register`

```python
register(
    name: str,
    check_fn: CheckFn[TContext, TIn, Any],
    description: str,
    media_type: str,
    *,
    metadata: GuardrailSpecMetadata | None = None,
) -> None
```

Register a new guardrail specification.

This adds a `:class:GuardrailSpec` to the registry, inferring the required context and configuration models from the function signature.

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| **`name`** | `str` | Unique identifier for the guardrail. | *required* |
| **`check_fn`** | `CheckFn` | Function that implements the guardrail logic. | *required* |
| **`description`** | `str` | Human-readable description for docs and discovery. | *required* |
| **`media_type`** | `str` | MIME type this guardrail operates on. | *required* |
| **`metadata`** | `GuardrailSpecMetadata` | Additional details for UIs or tooling. | `None` |

**Raises:**

| Type | Description |
| :--- | :--- |
| `ValueError` | If `media_type` is not a valid MIME type, or if `name` is already registered. |

**Example**

```python
registry.register(
    name="keyword_filter",
    check_fn=keywords,
    description="Triggers if text contains banned keywords.",
    media_type="text/plain",
)
```

*Source code in `src/guardrails/registry.py`*

---

### `remove`

```python
remove(name: str) -> None
```

Remove a registered guardrail specification by name.

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| **`name`** | `str` | The guardrail name to remove. | *required* |

**Raises:**

| Type | Description |
| :--- | :--- |
| `KeyError` | If `name` is not present in the registry. |

*Source code in `src/guardrails/registry.py`*

---

### `get`

```python
get(name: str) -> GuardrailSpec[Any, Any, Any]
```

Retrieve a registered guardrail specification by name.

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| **`name`** | `str` | The name passed to `:meth:register`. | *required* |

**Returns:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `GuardrailSpec` | `GuardrailSpec[Any, Any, Any]` | The registered guardrail specification. |

**Raises:**

| Type | Description |
| :--- | :--- |
| `KeyError` | If nothing is registered under `name`. |

*Source code in `src/guardrails/registry.py`*

---

### `get_all`

```python
get_all() -> list[GuardrailSpec[Any, Any, Any]]
```

Return a list of all registered guardrail specifications.

**Returns:**

| Type | Description |
| :--- | :--- |
| `list[GuardrailSpec[Any, Any, Any]]` | `list[GuardrailSpec]`: All registered specs, in registration order. |

*Source code in `src/guardrails/registry.py`*

---

### `get_all_metadata`

```python
get_all_metadata() -> list[Metadata]
```

Return summary metadata for all registered guardrail specifications.

This provides lightweight, serializable descriptions of all guardrails, suitable for documentation, UI display, or catalog listing.

**Returns:**

| Type | Description |
| :--- | :--- |
| `list[Metadata]` | `list[Metadata]`: List of metadata entries for each registered spec. |

*Source code in `src/guardrails/registry.py`*