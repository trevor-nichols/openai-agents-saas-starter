# Types: Python

Type definitions, Protocols, and result types for Guardrails.

This module provides core types for implementing Guardrails, including:

*   The `TokenUsage` dataclass, representing token consumption from LLM-based guardrails.
*   The `GuardrailResult` dataclass, representing the outcome of a guardrail check.
*   The `CheckFn` Protocol, a callable interface for all guardrail functions.

---

### `CheckFn` module-attribute

```python
CheckFn = Callable[
    [TContext, TIn, TCfg], MaybeAwaitableResult
]
```

Type alias for a guardrail function.

A guardrail function accepts a context object, input data, and a configuration object, returning either a `GuardrailResult` or an awaitable resolving to `GuardrailResult`.

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `TContext` | TypeVar | The context type (often includes resources used by a guardrail). | *required* |
| `TIn` | TypeVar | The input data to validate or check. | *required* |
| `TCfg` | TypeVar | The configuration type, usually a Pydantic model. | *required* |

**Returns:** `GuardrailResult` or `Awaitable[GuardrailResult]`: The outcome of the guardrail check.

---

## `TokenUsage` dataclass

Token usage statistics from an LLM-based guardrail.

This dataclass encapsulates token consumption data from OpenAI API responses. For providers that don't return usage data, the `unavailable_reason` field will contain an explanation.

**Attributes:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `prompt_tokens` | int \| None | Number of tokens in the prompt. `None` if unavailable. |
| `completion_tokens` | int \| None | Number of tokens in the completion. `None` if unavailable. |
| `total_tokens` | int \| None | Total tokens used. `None` if unavailable. |
| `unavailable_reason` | str \| None | Explanation when token usage is not available (e.g., third-party models). `None` when usage data is present. |

*Source code in `src/guardrails/types.py`*

---

## `GuardrailLLMContextProto`

**Bases:** `Protocol`

Protocol for context types providing an OpenAI client.

Classes implementing this protocol must expose an OpenAI client via the `guardrail_llm` attribute. For conversation-aware guardrails (like prompt injection detection), they can also access `conversation_history` containing the full conversation history.

**Attributes:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `guardrail_llm` | AsyncOpenAI \| OpenAI | The OpenAI client used by the guardrail. |
| `conversation_history` | list | Full conversation history for conversation-aware guardrails. |

*Source code in `src/guardrails/types.py`*

### `get_conversation_history`

```python
get_conversation_history() -> list | None
```

Get conversation history if available, `None` otherwise.

*Source code in `src/guardrails/types.py`*

---

## `GuardrailResult` dataclass

Result returned from a guardrail check.

This dataclass encapsulates the outcome of a guardrail function, including whether a tripwire was triggered, execution failure status, and any supplementary metadata.

**Attributes:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `tripwire_triggered` | bool | `True` if the guardrail identified a critical failure. |
| `execution_failed` | bool | `True` if the guardrail failed to execute properly. |
| `original_exception` | Exception \| None | The original exception if execution failed. |
| `info` | dict[str, Any] | Additional structured data about the check result, such as error details, matched patterns, or diagnostic messages. Implementations may include a `'checked_text'` field containing the processed/validated text when applicable. Defaults to an empty `dict`. |

*Source code in `src/guardrails/types.py`*

### `__post_init__`

```python
__post_init__() -> None
```

Validate required fields and consistency.

*Source code in `src/guardrails/types.py`*

---

### `extract_token_usage`

```python
extract_token_usage(response: Any) -> TokenUsage
```

Extract token usage from an OpenAI API response.

Attempts to extract token usage data from the response's `usage` attribute. Works with both Chat Completions API and Responses API responses. For third-party models or responses without usage data, returns a `TokenUsage` with `None` values and an explanation in `unavailable_reason`.

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `response` | Any | An OpenAI API response object (ChatCompletion, Response, etc.) | *required* |

**Returns:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `TokenUsage` | `TokenUsage` | Token usage statistics extracted from the response. |

*Source code in `src/guardrails/types.py`*

---

### `token_usage_to_dict`

```python
token_usage_to_dict(
    token_usage: TokenUsage,
) -> dict[str, Any]
```

Convert a `TokenUsage` dataclass to a dictionary for inclusion in `info` dicts.

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `token_usage` | TokenUsage | `TokenUsage` instance to convert. | *required* |

**Returns:**

| Type | Description |
| :--- | :--- |
| `dict[str, Any]` | Dictionary representation suitable for `GuardrailResult.info`. |

*Source code in `src/guardrails/types.py`*

---

### `aggregate_token_usage_from_infos`

```python
aggregate_token_usage_from_infos(
    info_dicts: Iterable[dict[str, Any] | None],
) -> dict[str, Any]
```

Aggregate token usage from multiple guardrail `info` dictionaries.

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `info_dicts` | Iterable[dict[str, Any] \| None] | Iterable of guardrail info dicts (each may contain a `token_usage` entry) or `None`. | *required* |

**Returns:**

| Type | Description |
| :--- | :--- |
| `dict[str, Any]` | Dictionary mirroring `GuardrailResults.total_token_usage` output. |

*Source code in `src/guardrails/types.py`*

---

### `total_guardrail_token_usage`

```python
total_guardrail_token_usage(result: Any) -> dict[str, Any]
```

Get aggregated token usage from any guardrails result object.

This is a unified interface that works across all guardrails surfaces:
- `GuardrailsResponse` (from `GuardrailsAsyncOpenAI`, `GuardrailsOpenAI`, etc.)
- `GuardrailResults` (direct access to organized results)
- Agents SDK `RunResult` (from `Runner.run` with `GuardrailAgent`)

**Parameters:**

| Name | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `result` | Any | A result object from any guardrails client. Can be: `GuardrailsResponse` with `guardrail_results` attribute, `GuardrailResults` with `total_token_usage` property, or Agents SDK `RunResult` with `*_guardrail_results` attributes. | *required* |

**Returns:**

| Type | Description |
| :--- | :--- |
| `dict[str, Any]` | Dictionary with aggregated token usage:<ul><li>`prompt_tokens`: Sum of all prompt tokens (or `None` if no data)</li><li>`completion_tokens`: Sum of all completion tokens (or `None` if no data)</li><li>`total_tokens`: Sum of all total tokens (or `None` if no data)</li></ul> |

**Example**

```python
# Works with OpenAI client responses
response = await client.responses.create(...)
tokens = total_guardrail_token_usage(response)

# Works with Agents SDK results
result = await Runner.run(agent, input)
tokens = total_guardrail_token_usage(result)

print(f"Used {tokens['total_tokens']} guardrail tokens")
```

*Source code in `src/guardrails/types.py`*