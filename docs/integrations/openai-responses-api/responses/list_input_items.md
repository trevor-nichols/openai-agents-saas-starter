## List input items

<div class="endpoint-header">
  <p class="endpoint-method">GET</p>
  <p class="endpoint-url">https://api.openai.com/v1/responses/{response_id}/input_items</p>
</div>

Returns a list of input items for a given response.

### Path parameters

-   **`response_id`** *string* `Required`
    The ID of the response to retrieve input items for.

### Query parameters

-   **`after`** *string* `Optional`
    An item ID to list items after, used in pagination.

-   **`include`** *array* `Optional`
    Additional fields to include in the response.

-   **`limit`** *integer* `Optional` `Defaults to 20`
    A limit on the number of objects to be returned (between 1 and 100).

-   **`order`** *string* `Optional`
    The order to return the input items in. `asc` or `desc` (default).

### Returns

A list of [input item objects](#the-input-item-list).

### Example request

```bash
curl https://api.openai.com/v1/responses/resp_abc123/input_items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "msg_abc123",
      "type": "message",
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "Tell me a three sentence bedtime story about a unicorn."
        }
      ]
    }
  ],
  "first_id": "msg_abc123",
  "last_id": "msg_abc123",
  "has_more": false
}
```

---

