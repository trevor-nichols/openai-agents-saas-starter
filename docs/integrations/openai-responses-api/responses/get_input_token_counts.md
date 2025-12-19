## Get input token counts

<div class="endpoint-header">
  <p class="endpoint-method">POST</p>
  <p class="endpoint-url">https://api.openai.com/v1/responses/input_tokens</p>
</div>

Returns input token counts of the request.

### Request body

-   **`conversation`** *string or object* `Optional`
    *(See `conversation` parameter in "Create a model response" for detailed structure.)*

-   **`input`** *string or array* `Optional`
    *(See `input` parameter in "Create a model response" for detailed structure.)*

-   **`instructions`** *string* `Optional`
    A system (or developer) message inserted into the model's context.

-   **`model`** *string* `Optional`
    Model ID used to generate the response.

-   **`parallel_tool_calls`** *boolean* `Optional`
    Whether to allow the model to run tool calls in parallel.

-   **`previous_response_id`** *string* `Optional`
    The unique ID of the previous response to the model.

-   **`reasoning`** *object* `Optional`
    *(See `reasoning` parameter in "Create a model response" for detailed structure.)*

-   **`text`** *object* `Optional`
    *(See `text` parameter in "Create a model response" for detailed structure.)*

-   **`tool_choice`** *string or object* `Optional`
    *(See `tool_choice` parameter in "Create a model response" for detailed structure.)*

-   **`tools`** *array* `Optional`
    *(See `tools` parameter in "Create a model response" for detailed structure.)*

-   **`truncation`** *string* `Optional`
    The truncation strategy to use for the model response.

### Returns

The input token counts.

```json
{
  "object": "response.input_tokens",
  "input_tokens": 123
}
```

### Example request

```bash
curl -X POST https://api.openai.com/v1/responses/input_tokens \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -d '{
      "model": "gpt-5",
      "input": "Tell me a joke."
    }'
```

### Response

```json
{
  "object": "response.input_tokens",
  "input_tokens": 11
}
```

---

