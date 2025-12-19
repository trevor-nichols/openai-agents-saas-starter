# Streaming Events - Output Content

## `response.output_item.added`
Emitted when a new output item is added.

<details>
<summary>Properties</summary>

-   **`item`** `object`
    The output item that was added.

-   **`output_index`** `integer`
    The index of the output item that was added.

-   **`sequence_number`** `integer`
    The sequence number of this event.

-   **`type`** `string`
    The type of the event. Always `response.output_item.added`.
</details>

**OBJECT `response.output_item.added`**
```json
{
  "type": "response.output_item.added",
  "output_index": 0,
  "item": {
    "id": "msg_123",
    "status": "in_progress",
    "type": "message",
    "role": "assistant",
    "content": []
  },
  "sequence_number": 1
}
```

---

## `response.output_item.done`
Emitted when an output item is marked done.

<details>
<summary>Properties</summary>

-   **`item`** `object`
    The output item that was marked done.

-   **`output_index`** `integer`
    The index of the output item that was marked done.

-   **`sequence_number`** `integer`
    The sequence number of this event.

-   **`type`** `string`
    The type of the event. Always `response.output_item.done`.
</details>

**OBJECT `response.output_item.done`**
```json
{
  "type": "response.output_item.done",
  "output_index": 0,
  "item": {
    "id": "msg_123",
    "status": "completed",
    "type": "message",
    "role": "assistant",
    "content": [
      {
        "type": "output_text",
        "text": "In a shimmering forest...",
        "annotations": []
      }
    ]
  },
  "sequence_number": 1
}
```

---

## `response.content_part.added`
Emitted when a new content part is added.

<details>
<summary>Properties</summary>

-   **`content_index`** `integer`
    The index of the content part that was added.
-   **`item_id`** `string`
    The ID of the output item that the content part was added to.
-   **`output_index`** `integer`
    The index of the output item that the content part was added to.
-   **`part`** `object`
    The content part that was added.
-   **`sequence_number`** `integer`
    The sequence number of this event.
-   **`type`** `string`
    The type of the event. Always `response.content_part.added`.
</details>

**OBJECT `response.content_part.added`**
```json
{
  "type": "response.content_part.added",
  "item_id": "msg_123",
  "output_index": 0,
  "content_index": 0,
  "part": {
    "type": "output_text",
    "text": "",
    "annotations": []
  },
  "sequence_number": 1
}```

---

## `response.content_part.done`
Emitted when a content part is done.

<details>
<summary>Properties</summary>

-   **`content_index`** `integer`
    The index of the content part that is done.
-   **`item_id`** `string`
    The ID of the output item that the content part was added to.
-   **`output_index`** `integer`
    The index of the output item that the content part was added to.
-   **`part`** `object`
    The content part that is done.
-   **`sequence_number`** `integer`
    The sequence number of this event.
-   **`type`** `string`
    The type of the event. Always `response.content_part.done`.
</details>

**OBJECT `response.content_part.done`**
```json
{
  "type": "response.content_part.done",
  "item_id": "msg_123",
  "output_index": 0,
  "content_index": 0,
  "sequence_number": 1,
  "part": {
    "type": "output_text",
    "text": "In a shimmering forest...",
    "annotations": []
  }
}
```

---

## `response.output_text.delta`
Emitted when there is an additional text delta.

<details>
<summary>Properties</summary>

-   **`content_index`** `integer`
    The index of the content part that the text delta was added to.
-   **`delta`** `string`
    The text delta that was added.
-   **`item_id`** `string`
    The ID of the output item that the text delta was added to.
-   **`logprobs`** `array`
    The log probabilities of the tokens in the delta.
-   **`output_index`** `integer`
    The index of the output item that the text delta was added to.
-   **`sequence_number`** `integer`
    The sequence number for this event.
-   **`type`** `string`
    The type of the event. Always `response.output_text.delta`.
</details>

**OBJECT `response.output_text.delta`**
```json
{
  "type": "response.output_text.delta",
  "item_id": "msg_123",
  "output_index": 0,
  "content_index": 0,
  "delta": "In",
  "sequence_number": 1
}
```

---

## `response.output_text.done`
Emitted when text content is finalized.

<details>
<summary>Properties</summary>

-   **`content_index`** `integer`
    The index of the content part that the text content is finalized.
-   **`item_id`** `string`
    The ID of the output item that the text content is finalized.
-   **`logprobs`** `array`
    The log probabilities of the tokens in the delta.
-   **`output_index`** `integer`
    The index of the output item that the text content is finalized.
-   **`sequence_number`** `integer`
    The sequence number for this event.
-   **`text`** `string`
    The text content that is finalized.
-   **`type`** `string`
    The type of the event. Always `response.output_text.done`.
</details>

**OBJECT `response.output_text.done`**
```json
{
  "type": "response.output_text.done",
  "item_id": "msg_123",
  "output_index": 0,
  "content_index": 0,
  "text": "In a shimmering forest...",
  "sequence_number": 1
}```

---

## `response.refusal.delta`
Emitted when there is a partial refusal text.

<details>
<summary>Properties</summary>

-   **`content_index`** `integer`
-   **`delta`** `string`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.refusal.delta`.
</details>

**OBJECT `response.refusal.delta`**
```json
{
  "type": "response.refusal.delta",
  "item_id": "msg_123",
  "output_index": 0,
  "content_index": 0,
  "delta": "refusal text so far",
  "sequence_number": 1
}
```

---

## `response.refusal.done`
Emitted when refusal text is finalized.

<details>
<summary>Properties</summary>

-   **`content_index`** `integer`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`refusal`** `string`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.refusal.done`.
</details>

**OBJECT `response.refusal.done`**
```json
{
  "type": "response.refusal.done",
  "item_id": "item-abc",
  "output_index": 1,
  "content_index": 2,
  "refusal": "final refusal text",
  "sequence_number": 1
}
```

---

## `response.output_text.annotation.added`
Emitted when an annotation is added to output text content.

<details>
<summary>Properties</summary>

-   **`annotation`** `object`
-   **`annotation_index`** `integer`
-   **`content_index`** `integer`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.output_text.annotation.added`.
</details>

**OBJECT `response.output_text.annotation.added`**
```json
{
  "type": "response.output_text.annotation.added",
  "item_id": "item-abc",
  "output_index": 0,
  "content_index": 0,
  "annotation_index": 0,
  "annotation": {
    "type": "text_annotation",
    "text": "This is a test annotation",
    "start": 0,
    "end": 10
  },
  "sequence_number": 1
}
```

