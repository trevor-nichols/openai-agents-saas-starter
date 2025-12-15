## The input item list

A list of Response items.

-   **`data`** *array*
    A list of items used to generate this response.
    *(See `Item` object in "Create a model response" for detailed structure.)*

-   **`first_id`** *string*
    The ID of the first item in the list.

-   **`has_more`** *boolean*
    Whether there are more items available.

-   **`last_id`** *string*
    The ID of the last item in the list.

-   **`object`** *string*
    The type of object returned, must be `list`.

### OBJECT The input item list

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

