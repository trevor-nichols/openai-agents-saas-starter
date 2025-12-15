# Streaming Events - Function Calls

## `response.function_call_arguments.delta`
Emitted when there is a partial function-call arguments delta.

<details>
<summary>Properties</summary>

-   **`delta`** `string`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.function_call_arguments.delta`.
</details>

**OBJECT `response.function_call_arguments.delta`**
```json
{
  "type": "response.function_call_arguments.delta",
  "item_id": "item-abc",
  "output_index": 0,
  "delta": "{ \"arg\":",
  "sequence_number": 1
}
```

---

## `response.function_call_arguments.done`
Emitted when function-call arguments are finalized.

<details>
<summary>Properties</summary>

-   **`arguments`** `string`
-   **`item_id`** `string`
-   **`name`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string`
</details>

**OBJECT `response.function_call_arguments.done`**
```json
{
  "type": "response.function_call_arguments.done",
  "item_id": "item-abc",
  "name": "get_weather",
  "output_index": 1,
  "arguments": "{ \"arg\": 123 }",
  "sequence_number": 1
}
```

---

## `response.custom_tool_call_input.delta`
Event representing a delta (partial update) to the input of a custom tool call.

<details>
<summary>Properties</summary>

-   **`delta`** `string`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string`
</details>

**OBJECT `response.custom_tool_call_input.delta`**
```json
{
  "type": "response.custom_tool_call_input.delta",
  "output_index": 0,
  "item_id": "ctc_1234567890abcdef",
  "delta": "partial input text"
}
```

---

## `response.custom_tool_call_input.done`
Event indicating that input for a custom tool call is complete.

<details>
<summary>Properties</summary>

-   **`input`** `string`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string`
</details>

**OBJECT `response.custom_tool_call_input.done`**
```json
{
  "type": "response.custom_tool_call_input.done",
  "output_index": 0,
  "item_id": "ctc_1234567890abcdef",
  "input": "final complete input text"
}
```

