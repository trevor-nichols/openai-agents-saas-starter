# Streaming Events - Reasoning

## `response.reasoning_summary_part.added`
Emitted when a new reasoning summary part is added.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`part`** `object`
    <details>
    <summary>Properties</summary>
    - **`text`** `string`
    - **`type`** `string` - Always `summary_text`.
    </details>
-   **`sequence_number`** `integer`
-   **`summary_index`** `integer`
-   **`type`** `string` - Always `response.reasoning_summary_part.added`.
</details>

**OBJECT `response.reasoning_summary_part.added`**
```json
{
  "type": "response.reasoning_summary_part.added",
  "item_id": "rs_6806bfca0b2481918a5748308061a2600d3ce51bdffd5476",
  "output_index": 0,
  "summary_index": 0,
  "part": {
    "type": "summary_text",
    "text": ""
  },
  "sequence_number": 1
}
```

---

## `response.reasoning_summary_part.done`
Emitted when a reasoning summary part is completed.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`part`** `object`
    <details>
    <summary>Properties</summary>
    - **`text`** `string`
    - **`type`** `string` - Always `summary_text`.
    </details>
-   **`sequence_number`** `integer`
-   **`summary_index`** `integer`
-   **`type`** `string` - Always `response.reasoning_summary_part.done`.
</details>

**OBJECT `response.reasoning_summary_part.done`**
```json
{
  "type": "response.reasoning_summary_part.done",
  "item_id": "rs_6806bfca0b2481918a5748308061a2600d3ce51bdffd5476",
  "output_index": 0,
  "summary_index": 0,
  "part": {
    "type": "summary_text",
    "text": "**Responding to a greeting**\n\nThe user just said, \"Hello!\"..."
  },
  "sequence_number": 1
}
```

---

## `response.reasoning_summary_text.delta`
Emitted when a delta is added to a reasoning summary text.

<details>
<summary>Properties</summary>

-   **`delta`** `string`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`summary_index`** `integer`
-   **`type`** `string` - Always `response.reasoning_summary_text.delta`.
</details>

**OBJECT `response.reasoning_summary_text.delta`**
```json
{
  "type": "response.reasoning_summary_text.delta",
  "item_id": "rs_6806bfca0b2481918a5748308061a2600d3ce51bdffd5476",
  "output_index": 0,
  "summary_index": 0,
  "delta": "**Responding to a greeting**...",
  "sequence_number": 1
}
```

---

## `response.reasoning_summary_text.done`
Emitted when a reasoning summary text is completed.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`summary_index`** `integer`
-   **`text`** `string`
-   **`type`** `string` - Always `response.reasoning_summary_text.done`.
</details>

**OBJECT `response.reasoning_summary_text.done`**
```json
{
  "type": "response.reasoning_summary_text.done",
  "item_id": "rs_6806bfca0b2481918a5748308061a2600d3ce51bdffd5476",
  "output_index": 0,
  "summary_index": 0,
  "text": "**Responding to a greeting**\n\nThe user just said, \"Hello!\"...",
  "sequence_number": 1
}
```

---

## `response.reasoning_text.delta`
Emitted when a delta is added to a reasoning text.

<details>
<summary>Properties</summary>

-   **`content_index`** `integer`
-   **`delta`** `string`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.reasoning_text.delta`.
</details>

**OBJECT `response.reasoning_text.delta`**
```json
{
  "type": "response.reasoning_text.delta",
  "item_id": "rs_123",
  "output_index": 0,
  "content_index": 0,
  "delta": "The",
  "sequence_number": 1
}
```

---

## `response.reasoning_text.done`
Emitted when a reasoning text is completed.

<details>
<summary>Properties</summary>

-   **`content_index`** `integer`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`text`** `string`
-   **`type`** `string` - Always `response.reasoning_text.done`.
</details>

**OBJECT `response.reasoning_text.done`**
```json
{
  "type": "response.reasoning_text.done",
  "item_id": "rs_123",
  "output_index": 0,
  "content_index": 0,
  "text": "The user is asking...",
  "sequence_number": 4
}
```

