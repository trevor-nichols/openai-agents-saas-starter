## Get a model response

<div class="endpoint-header">
  <p class="endpoint-method">GET</p>
  <p class="endpoint-url">https://api.openai.com/v1/responses/{response_id}</p>
</div>

Retrieves a model response with the given ID.

### Path parameters

-   **`response_id`** *string* `Required`
    The ID of the response to retrieve.

### Query parameters

-   **`include`** *array* `Optional`
    Additional fields to include in the response. See the `include` parameter for Response creation above for more information.

-   **`include_obfuscation`** *boolean* `Optional`
    When true, stream obfuscation will be enabled.

-   **`starting_after`** *integer* `Optional`
    The sequence number of the event after which to start streaming.

-   **`stream`** *boolean* `Optional`
    If set to true, the model response data will be streamed to the client as it is generated using server-sent events.

### Returns

The [Response object](#the-response-object) matching the specified ID.

### Example request

```bash
curl https://api.openai.com/v1/responses/resp_123 \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Response

```json
{
  "id": "resp_67cb71b351908190a308f3859487620d06981a8637e6bc44",
  "object": "response",
  "created_at": 1741386163,
  "status": "completed",
  "error": null,
  "incomplete_details": null,
  "instructions": null,
  "max_output_tokens": null,
  "model": "gpt-4o-2024-08-06",
  "output": [
    {
      "type": "message",
      "id": "msg_67cb71b3c2b0819084d481baaaf148f206981a8637e6bc44",
      "status": "completed",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "Silent circuits hum,  \nThoughts emerge in data streams—  \nDigital dawn breaks.",
          "annotations": []
        }
      ]
    }
  ],
  "parallel_tool_calls": true,
  "previous_response_id": null,
  "reasoning": {
    "effort": null,
    "summary": null
  },
  "store": true,
  "temperature": 1.0,
  "text": {
    "format": {
      "type": "text"
    }
  },
  "tool_choice": "auto",
  "tools": [],
  "top_p": 1.0,
  "truncation": "disabled",
  "usage": {
    "input_tokens": 32,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 18,
    "output_tokens_details": {
      "reasoning_tokens": 0
    },
    "total_tokens": 50
  },
  "user": null,
  "metadata": {}
}
```

---

