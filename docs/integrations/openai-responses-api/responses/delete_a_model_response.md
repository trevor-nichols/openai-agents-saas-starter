## Delete a model response

<div class="endpoint-header">
  <p class="endpoint-method">DELETE</p>
  <p class="endpoint-url">https://api.openai.com/v1/responses/{response_id}</p>
</div>

Deletes a model response with the given ID.

### Path parameters

-   **`response_id`** *string* `Required`
    The ID of the response to delete.

### Returns

A success message.

### Example request

```bash
curl -X DELETE https://api.openai.com/v1/responses/resp_123 \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Response

```json
{
  "id": "resp_6786a1bec27481909a17d673315b29f6",
  "object": "response",
  "deleted": true
}
```

---

