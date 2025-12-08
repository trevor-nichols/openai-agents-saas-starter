# Exceptions: Python

## Exception classes used throughout Guardrails for SDK and model errors.

---

### `GuardrailException`
> **Bases:** `Exception`

Base class for exceptions thrown by `:mod:guardrails`.

*Source code in `src/guardrails/exceptions.py`*

---

### `UserError`
> **Bases:** `GuardrailException`

Error raised when the user misuses the SDK.

*Source code in `src/guardrails/exceptions.py`*

#### `__init__`
```python
__init__(message: str)
```
Initialize the exception with a human readable message.

*Source code in `src/guardrails/exceptions.py`*

---

### `ModelBehaviorError`
> **Bases:** `GuardrailException`

Error raised when the model returns malformed or invalid data.

*Source code in `src/guardrails/exceptions.py`*

#### `__init__`
```python
__init__(message: str)
```
Initialize with information on the misbehaviour.

*Source code in `src/guardrails/exceptions.py`*

---

### `GuardrailTripwireTriggered`
> **Bases:** `GuardrailException`

Raised when a guardrail triggers a configured tripwire.

*Source code in `src/guardrails/exceptions.py`*

#### `guardrail_result` instance-attribute
```python
guardrail_result: GuardrailResult = guardrail_result
```
The result data from the triggering guardrail.

#### `__init__`
```python
__init__(guardrail_result: GuardrailResult)
```
Initialize storing the result which caused the tripwire.

*Source code in `src/guardrails/exceptions.py`*

---

### `ConfigError`
> **Bases:** `GuardrailException`

Configuration bundle could not be loaded or validated.

*Source code in `src/guardrails/exceptions.py`*

#### `__init__`
```python
__init__(message: str)
```
Initialize with a short description of the failure.

*Source code in `src/guardrails/exceptions.py`*

---

### `ContextValidationError`
> **Bases:** `GuardrailException`

Raised when CLI context fails to match guardrail specification.

*Source code in `src/guardrails/exceptions.py`*

#### `__init__`
```python
__init__(message: str)
```
Initialize with details about the schema mismatch.

*Source code in `src/guardrails/exceptions.py`*