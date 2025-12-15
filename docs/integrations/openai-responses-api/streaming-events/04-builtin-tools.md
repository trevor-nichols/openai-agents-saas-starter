# Streaming Events - OpenAI Hosted Tools

## `response.file_search_call.in_progress`
Emitted when a file search call is initiated.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.file_search_call.in_progress`.
</details>

**OBJECT `response.file_search_call.in_progress`**
```json
{
  "type": "response.file_search_call.in_progress",
  "output_index": 0,
  "item_id": "fs_123",
  "sequence_number": 1
}
```

---

## `response.file_search_call.searching`
Emitted when a file search is currently searching.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.file_search_call.searching`.
</details>

**OBJECT `response.file_search_call.searching`**
```json
{
  "type": "response.file_search_call.searching",
  "output_index": 0,
  "item_id": "fs_123",
  "sequence_number": 1
}
```

---

## `response.file_search_call.completed`
Emitted when a file search call is completed (results found).

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.file_search_call.completed`.
</details>

**OBJECT `response.file_search_call.completed`**
```json
{
  "type": "response.file_search_call.completed",
  "output_index": 0,
  "item_id": "fs_123",
  "sequence_number": 1
}
```

---

## `response.web_search_call.in_progress`
Emitted when a web search call is initiated.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.web_search_call.in_progress`.
</details>

**OBJECT `response.web_search_call.in_progress`**
```json
{
  "type": "response.web_search_call.in_progress",
  "output_index": 0,
  "item_id": "ws_123",
  "sequence_number": 0
}
```

---

## `response.web_search_call.searching`
Emitted when a web search call is executing.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.web_search_call.searching`.
</details>

**OBJECT `response.web_search_call.searching`**
```json
{
  "type": "response.web_search_call.searching",
  "output_index": 0,
  "item_id": "ws_123",
  "sequence_number": 0
}
```

---

## `response.web_search_call.completed`
Emitted when a web search call is completed.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.web_search_call.completed`.
</details>

**OBJECT `response.web_search_call.completed`**
```json
{
  "type": "response.web_search_call.completed",
  "output_index": 0,
  "item_id": "ws_123",
  "sequence_number": 0
}
```

---

## `response.image_generation_call.completed`
Emitted when an image generation tool call has completed and the final image is available.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.image_generation_call.completed`.
</details>

**OBJECT `response.image_generation_call.completed`**
```json
{
  "type": "response.image_generation_call.completed",
  "output_index": 0,
  "item_id": "item-123",
  "sequence_number": 1
}
```

---

## `response.image_generation_call.generating`
Emitted when an image generation tool call is actively generating an image.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.image_generation_call.generating`.
</details>

**OBJECT `response.image_generation_call.generating`**
```json
{
  "type": "response.image_generation_call.generating",
  "output_index": 0,
  "item_id": "item-123",
  "sequence_number": 0
}
```

---

## `response.image_generation_call.in_progress`
Emitted when an image generation tool call is in progress.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.image_generation_call.in_progress`.
</details>

**OBJECT `response.image_generation_call.in_progress`**
```json
{
  "type": "response.image_generation_call.in_progress",
  "output_index": 0,
  "item_id": "item-123",
  "sequence_number": 0
}
```

---

## `response.image_generation_call.partial_image`
Emitted when a partial image is available during image generation streaming.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`partial_image_b64`** `string`
-   **`partial_image_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.image_generation_call.partial_image`.
</details>

**OBJECT `response.image_generation_call.partial_image`**
```json
{
  "type": "response.image_generation_call.partial_image",
  "output_index": 0,
  "item_id": "item-123",
  "sequence_number": 0,
  "partial_image_index": 0,
  "partial_image_b64": "..."
}
```

---

## `response.code_interpreter_call.in_progress`
Emitted when a code interpreter call is in progress.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.code_interpreter_call.in_progress`.
</details>

**OBJECT `response.code_interpreter_call.in_progress`**
```json
{
  "type": "response.code_interpreter_call.in_progress",
  "output_index": 0,
  "item_id": "ci_12345",
  "sequence_number": 1
}
```

---

## `response.code_interpreter_call.interpreting`
Emitted when the code interpreter is actively interpreting the code snippet.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.code_interpreter_call.interpreting`.
</details>

**OBJECT `response.code_interpreter_call.interpreting`**
```json
{
  "type": "response.code_interpreter_call.interpreting",
  "output_index": 4,
  "item_id": "ci_12345",
  "sequence_number": 1
}
```

---

## `response.code_interpreter_call.completed`
Emitted when the code interpreter call is completed.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.code_interpreter_call.completed`.
</details>

**OBJECT `response.code_interpreter_call.completed`**
```json
{
  "type": "response.code_interpreter_call.completed",
  "output_index": 5,
  "item_id": "ci_12345",
  "sequence_number": 1
}
```

---

## `response.code_interpreter_call_code.delta`
Emitted when a partial code snippet is streamed by the code interpreter.

<details>
<summary>Properties</summary>

-   **`delta`** `string`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.code_interpreter_call_code.delta`.
</details>

**OBJECT `response.code_interpreter_call_code.delta`**
```json
{
  "type": "response.code_interpreter_call_code.delta",
  "output_index": 0,
  "item_id": "ci_12345",
  "delta": "print('Hello, world')",
  "sequence_number": 1
}
```

---

## `response.code_interpreter_call_code.done`
Emitted when the code snippet is finalized by the code interpreter.

<details>
<summary>Properties</summary>

-   **`code`** `string`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.code_interpreter_call_code.done`.
</details>

**OBJECT `response.code_interpreter_call_code.done`**
```json
{
  "type": "response.code_interpreter_call_code.done",
  "output_index": 3,
  "item_id": "ci_12345",
  "code": "print('done')",
  "sequence_number": 1
}
```

