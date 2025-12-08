# Runtime
Helpers for loading configuration bundles and running guardrails.

This module is the bridge between configuration and runtime execution for guardrail validation. It provides pure helpers for loading config bundles, instantiating guardrails from registry specs, and orchestrating parallel execution of guardrail checks. All logic is pure and side-effect-free except for I/O during config reading.

---

## `ConfiguredGuardrail` dataclass
**Bases:** `Generic[TContext, TIn, TCfg]`

A configured, executable guardrail.

This class binds a `GuardrailSpec` definition to a validated configuration object. The resulting instance is used to run guardrail logic in production pipelines. It supports both sync and async check functions.

**Attributes:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `definition` | `GuardrailSpec[TContext, TIn, TCfg]` | The immutable guardrail specification. |
| `config` | `TCfg` | Validated user configuration for this instance. |

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)

### `run` async
```python
run(ctx: TContext, data: TIn) -> GuardrailResult
```
Run the guardrail's check function with the provided context and data.

Main entry point for executing guardrails. Supports both sync and async functions, ensuring results are always awaited.

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `ctx` | `TContext` | Runtime context for the guardrail. | *required* |
| `data` | `TIn` | Input value to be checked. | *required* |

**Returns:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `GuardrailResult` | `GuardrailResult` | The outcome of the guardrail logic. |

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)

---

## `GuardrailConfig`
**Bases:** `BaseModel`

Configuration for a single guardrail instance.

Used for serializing, deserializing, and validating guardrail configs as part of a bundle.

**Attributes:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | The registry name used to look up the guardrail spec. |
| `config` | `dict[str, Any]` | Raw user configuration for this guardrail. |

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)

---

## `ConfigBundle`
**Bases:** `BaseModel`

Versioned collection of configured guardrails.

Represents a serializable "bundle" of guardrails to be run as a unit. Suitable for JSON storage and loading.

**Attributes:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `guardrails` | `list[GuardrailConfig]` | The configured guardrails. |
| `version` | `int` | Format version for forward/backward compatibility. |
| `config` | `dict[str, Any]` | Execution configuration for this bundle. Optional fields include: <br>- `concurrency` (int): Maximum number of guardrails to run in parallel (default: 10) <br>- `suppress_tripwire` (bool): If True, don't raise exceptions on tripwires (default: False) |

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)

---

## `PipelineBundles`
**Bases:** `BaseModel`

Three-stage collection of validated `ConfigBundles` for an LLM pipeline.

This class groups together guardrail configurations for the three main pipeline stages:

-   `pre_flight`: Checks that run before the LLM request is issued.
-   `input`: Checks on the user's prompt (may run concurrently with LLM call).
-   `output`: Checks on incremental LLM output.

At least one stage must be provided, but all stages are optional.

**Attributes:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `pre_flight` | `ConfigBundle | None` | Guardrails to run before the LLM request. |
| `input` | `ConfigBundle | None` | Guardrails to run on user input. |
| `output` | `ConfigBundle | None` | Guardrails to run on generated output. |
| `version` | `int` | Schema version for the envelope itself. Defaults to 1. |

**Example**

```python
# All stages
pipeline = PipelineBundles(
    pre_flight=load_config_bundle(PRE_FLIGHT),
    input=load_config_bundle(INPUT_BUNDLE),
    output=load_config_bundle(OUTPUT_BUNDLE),
)

# Just output stage
pipeline = PipelineBundles(
    output=load_config_bundle(OUTPUT_BUNDLE),
)

# Print active stages
for stage in pipeline.stages():
    print(stage.version)
```

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)

### `model_post_init`
```python
model_post_init(__context: Any) -> None
```
Validate that at least one stage is provided.

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)

### `stages`
```python
stages() -> tuple[ConfigBundle, ...]
```
Return non-None bundles in execution order (pre_flight → input → output).

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)

---

## `JsonString` dataclass
Explicit wrapper to mark a string as a raw JSON config.

Used to distinguish JSON string inputs from other config sources (path/dict).

**Attributes:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `content` | `str` | The raw JSON string. |

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)

---

## `load_config_bundle`
```python
load_config_bundle(source: ConfigSource) -> ConfigBundle
```
Load a `ConfigBundle` from a path, dict, JSON string, or already-parsed object.

**Supported sources**
-   `ConfigBundle`: Already validated bundle.
-   `dict`: Raw data, parsed as `ConfigBundle`.
-   `Path`: JSON file on disk.
-   `JsonString`: Raw JSON string.

**Example usage**
```python
bundle = load_config_bundle(JsonString('{"guardrails": [...]}'))
bundle = load_config_bundle({"guardrails": [...]})
bundle = load_config_bundle(Path("./config.json"))
```

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `source` | `ConfigSource` | Config bundle input. | *required* |

**Raises:**

| Type | Description |
| :--- | :--- |
| `ConfigError` | If loading fails. |
| `ValidationError` | If model validation fails. |
| `FileNotFoundError` | If file doesn't exist. |

**Returns:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `ConfigBundle` | `ConfigBundle` | The loaded and validated configuration bundle. |

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)

---

## `load_pipeline_bundles`
```python
load_pipeline_bundles(source: PipelineSource) -> PipelineBundles
```
Load a `PipelineBundles` from a path, dict, JSON string, or already-parsed object.

**Supported sources**
-   `PipelineBundles`: Already validated pipeline bundles.
-   `dict`: Raw data, parsed as `PipelineBundles`.
-   `Path`: JSON file on disk.
-   `JsonString`: Raw JSON string.

**Example usage**
```python
bundle = load_pipeline_bundles(JsonString('{"pre_flight": {...}, ...}'))
bundle = load_pipeline_bundles({"pre_flight": {...}, ...})
bundle = load_pipeline_bundles(Path("./pipeline.json"))
```

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `source` | `PipelineSource` | Pipeline bundles input. | *required* |

**Raises:**

| Type | Description |
| :--- | :--- |
| `ConfigError` | If loading fails. |
| `ValidationError` | If model validation fails. |
| `FileNotFoundError` | If file doesn't exist. |

**Returns:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `PipelineBundles` | `PipelineBundles` | The loaded and validated pipeline configuration bundle. |

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)

---

## `instantiate_guardrails`
```python
instantiate_guardrails(
    bundle: ConfigBundle,
    registry: GuardrailRegistry | None = None,
) -> list[ConfiguredGuardrail[Any, Any, Any]]
```
Instantiate all configured guardrails in a bundle as executable objects.

This function validates each guardrail configuration, retrieves the spec from the registry, and returns a list of fully configured guardrails.

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `bundle` | `ConfigBundle` | The validated configuration bundle. | *required* |
| `registry` | `GuardrailRegistry` | Registry mapping names to specs. If not provided, defaults to `default_spec_registry`. | `None` |

**Raises:**

| Type | Description |
| :--- | :--- |
| `ConfigError` | If any individual guardrail config is invalid. |

**Returns:**

| Type | Description |
| :--- | :--- |
| `list[ConfiguredGuardrail[Any, Any, Any]]` | `list[ConfiguredGuardrail[Any, Any, Any]]`: All configured/runnable guardrail objects. |

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)

---

## `run_guardrails` async
```python
run_guardrails(
    ctx: TContext,
    data: TIn,
    media_type: str,
    guardrails: Iterable[
        ConfiguredGuardrail[TContext, TIn, Any]
    ],
    *,
    concurrency: int = 10,
    result_handler: Callable[
        [GuardrailResult], Coroutine[None, None, None]
    ]
    | None = None,
    suppress_tripwire: bool = False,
    stage_name: str | None = None,
    raise_guardrail_errors: bool = False,
) -> list[GuardrailResult]
```
Run a set of configured guardrails concurrently and collect their results.

Validates context requirements for each guardrail, filters guardrails by the specified media type, and runs each check function concurrently, up to the specified concurrency limit. Results for all executed guardrails are collected and returned in order. If any guardrail triggers a tripwire, the function will raise a `GuardrailTripwireTriggered` exception unless tripwire suppression is enabled.

An optional asynchronous result handler can be provided to perform side effects (e.g., logging, custom result processing) for each guardrail result as it becomes available.

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `ctx` | `TContext` | Context object passed to all guardrail checks. Must satisfy all required fields specified by each guardrail's context schema. | *required* |
| `data` | `TIn` | The input to be validated by the guardrails. | *required* |
| `media_type` | `str` | MIME type used to filter which guardrails to execute. (e.g. "text/plain") | *required* |
| `guardrails` | `Iterable[ConfiguredGuardrail[TContext, TIn, Any]]` | Iterable of configured guardrails to run. | *required* |
| `concurrency` | `int` | Maximum number of guardrails to run in parallel. Defaults to 10. | `10` |
| `result_handler` | `Callable[[GuardrailResult], Awaitable[None]]` | Asynchronous callback function to be invoked for each guardrail result as it is produced. Defaults to None. | `None` |
| `suppress_tripwire` | `bool` | If True, tripwire-triggered results are included in the returned list and no exception is raised. If False (default), the function aborts and raises `GuardrailTripwireTriggered` on the first tripwire. | `False` |
| `stage_name` | `str | None` | Name of the pipeline stage (e.g., "pre_flight", "input", "output"). If provided, this will be included in the `GuardrailResult` info. Defaults to None. | `None` |
| `raise_guardrail_errors` | `bool` | If True, raise exceptions when guardrails fail to execute. If False (default), treat guardrail execution errors as safe and continue execution. | `False` |

**Returns:**

| Type | Description |
| :--- | :--- |
| `list[GuardrailResult]` | `list[GuardrailResult]`: List of results for all executed guardrails. If tripwire suppression is disabled (default) and a tripwire is triggered, only results up to the first tripwire may be included. |

**Raises:**

| Type | Description |
| :--- | :--- |
| `GuardrailTripwireTriggered` | Raised if a guardrail tripwire is triggered and `suppress_tripwire` is False. |
| `ContextValidationError` | Raised if the provided context does not meet requirements for any guardrail being executed. |

**Example**
```python
results = await run_guardrails(
    ctx=my_ctx,
    data="example input",
    media_type="text/plain",
    guardrails=my_guardrails,
    concurrency=4,
    suppress_tripwire=True,
    stage_name="input",
)
```

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)

---

## `check_plain_text` async
```python
check_plain_text(
    text: str,
    bundle_path: ConfigSource = Path("guardrails.json"),
    registry: GuardrailRegistry | None = None,
    ctx: Any = None,
    **kwargs: Any,
) -> list[GuardrailResult]
```
Validate plain text input against all configured guardrails for the 'text/plain' media type.

This function loads a guardrail configuration bundle, instantiates all guardrails for the specified registry, and runs each guardrail against the provided text input. It is the recommended entry point for validating plain text with one or more guardrails in an async context.

If no context object (`ctx`) is provided, a minimal default context will be constructed with attributes required by the guardrails' context schema (for example, an OpenAI client and any required fields with safe default values). For advanced use cases, you can supply your own context object.

Keyword arguments are forwarded to `run_guardrails`, allowing you to control concurrency, provide a result handler, or suppress tripwire exceptions.

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `text` | `str` | The plain text input to validate. | *required* |
| `bundle_path` | `ConfigSource` | Guardrail configuration bundle. This can be a file path, dict, JSON string, or `ConfigBundle` instance. Defaults to "guardrails.json". | `Path('guardrails.json')` |
| `registry` | `GuardrailRegistry` | Guardrail registry to use for instantiation. If not provided, the default registry is used. | `None` |
| `ctx` | `Any` | Application context object passed to each guardrail. If None (default), a minimal default context will be used. | `None` |
| `**kwargs` | `Any` | Additional keyword arguments forwarded to `run_guardrails`. Common options include:<br>- `concurrency` (int): Maximum number of guardrails to run concurrently.<br>- `result_handler` (Callable[[GuardrailResult], Awaitable[None]]): Async function invoked for each result.<br>- `suppress_tripwire` (bool): If True, do not raise an exception on tripwire; instead, return all results. | `{}` |

**Returns:**

| Type | Description |
| :--- | :--- |
| `list[GuardrailResult]` | `list[GuardrailResult]`: Results from all executed guardrails. |

**Raises:**

| Type | Description |
| :--- | :--- |
| `ConfigError` | If the configuration bundle cannot be loaded or is invalid. |
| `ContextValidationError` | If the context does not meet required fields for the guardrails. |
| `GuardrailTripwireTriggered` | If a guardrail tripwire is triggered and `suppress_tripwire` is False. |

**Example**
```python
from guardrails import check_plain_text

results = await check_plain_text(
    "some text",
    bundle_path="my_guardrails.json",
    concurrency=4,
    suppress_tripwire=True,
)
```

[Source code in `src/guardrails/runtime.py`](src/guardrails/runtime.py)