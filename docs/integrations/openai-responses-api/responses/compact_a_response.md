## Compact a response

<div class="endpoint-header">
  <p class="endpoint-method">POST</p>
  <p class="endpoint-url">https://api.openai.com/v1/responses/compact</p>
</div>

Runs a compaction pass over a conversation. Compaction returns encrypted, opaque items and the underlying logic may evolve over time.

### Request body

-   **`model`** *string* `Required`
    Model ID used to generate the response, like `gpt-5` or `o3`.

-   **`input`** *string or array* `Optional`
    Text, image, or file inputs to the model.
    *(See `input` parameter in "Create a model response" for detailed structure.)*

-   **`instructions`** *string* `Optional`
    A system (or developer) message inserted into the model's context.

-   **`previous_response_id`** *string* `Optional`
    The unique ID of the previous response to the model. Cannot be used in conjunction with `conversation`.

### Returns

A [compacted response object](#the-compacted-response-object).

Learn when and how to compact long-running conversations in the [conversation state guide](https://platform.openai.com/docs/guides/responses/conversation-state).

### Example request

```bash
curl -X POST https://api.openai.com/v1/responses/compact \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -d '{
      "model": "gpt-5.1-codex-max",
      "input": [
        {
          "role": "user",
          "content": "Create a simple landing page for a dog petting café."
        },
        {
          "id": "msg_001",
          "type": "message",
          "status": "completed",
          "content": [
            {
              "type": "output_text",
              "annotations": [],
              "logprobs": [],
              "text": "Below is a single file, ready-to-use landing page for a dog petting café:..."
            }
          ],
          "role": "assistant"
        }
      ]
    }'
```

### Response

```json
{
  "id": "resp_001",
  "object": "response.compaction",
  "created_at": 1764967971,
  "output": [
    {
      "id": "msg_000",
      "type": "message",
      "status": "completed",
      "content": [
        {
          "type": "input_text",
          "text": "Create a simple landing page for a dog petting cafe."
        }
      ],
      "role": "user"
    },
    {
      "id": "cmp_001",
      "type": "compaction",
      "encrypted_content": "gAAAAABpM0Yj-...="
    }
  ],
  "usage": {
    "input_tokens": 139,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 438,
    "output_tokens_details": {
      "reasoning_tokens": 64
    },
    "total_tokens": 577
  }
}
```

---

