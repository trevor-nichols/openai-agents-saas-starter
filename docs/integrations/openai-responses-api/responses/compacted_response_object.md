## The compacted response object

-   **`created_at`** *integer*
    Unix timestamp (in seconds) when the compacted conversation was created.

-   **`id`** *string*
    The unique identifier for the compacted response.

-   **`object`** *string*
    The object type. Always `response.compaction`.

-   **`output`** *array*
    The compacted list of output items.
    *(See `Item` object in "Create a model response" for detailed structure, with a `compaction` item type being possible.)*

-   **`usage`** *object*
    Token usage details for the compaction process.
    -   **`input_tokens`** *integer*
    -   **`input_tokens_details`** *object*
        -   **`cached_tokens`** *integer*
    -   **`output_tokens`** *integer*
    -   **`output_tokens_details`** *object*
        -   **`reasoning_tokens`** *integer*
    -   **`total_tokens`** *integer*

### OBJECT The compacted response object

```json
{
  "id": "resp_001",
  "object": "response.compaction",
  "output": [
    {
      "type": "message",
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "Summarize our launch checklist from last week."
        }
      ]
    },
    {
      "type": "message",
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "You are performing a CONTEXT CHECKPOINT COMPACTION..."
        }
      ]
    },
    {
      "type": "compaction",
      "id": "cmp_001",
      "encrypted_content": "encrypted-summary"
    }
  ],
  "created_at": 1731459200,
  "usage": {
    "input_tokens": 42897,
    "output_tokens": 12000,
    "total_tokens": 54912
  }
}
```