# Streaming Events - Errors

## `error`
Emitted when an error occurs.

<details>
<summary>Properties</summary>

-   **`code`** `string`
-   **`message`** `string`
-   **`param`** `string`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `error`.
</details>

**OBJECT `error`**
```json
{
  "type": "error",
  "code": "ERR_SOMETHING",
  "message": "Something went wrong",
  "param": null,
  "sequence_number": 1
}
```

```
