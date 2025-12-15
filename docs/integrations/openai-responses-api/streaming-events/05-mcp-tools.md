# Streaming Events - MCP Tools

## `response.mcp_call_arguments.delta`
Emitted when there is a delta to the arguments of an MCP tool call.

<details>
<summary>Properties</summary>

-   **`delta`** `string`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.mcp_call_arguments.delta`.
</details>

**OBJECT `response.mcp_call_arguments.delta`**
```json
{
  "type": "response.mcp_call_arguments.delta",
  "output_index": 0,
  "item_id": "item-abc",
  "delta": "{",
  "sequence_number": 1
}
```

---

## `response.mcp_call_arguments.done`
Emitted when the arguments for an MCP tool call are finalized.

<details>
<summary>Properties</summary>

-   **`arguments`** `string`
-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.mcp_call_arguments.done`.
</details>

**OBJECT `response.mcp_call_arguments.done`**
```json
{
  "type": "response.mcp_call_arguments.done",
  "output_index": 0,
  "item_id": "item-abc",
  "arguments": "{\"arg1\": \"value1\", \"arg2\": \"value2\"}",
  "sequence_number": 1
}```

---

## `response.mcp_call.completed`
Emitted when an MCP tool call has completed successfully.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.mcp_call.completed`.
</details>

**OBJECT `response.mcp_call.completed`**
```json
{
  "type": "response.mcp_call.completed",
  "sequence_number": 1,
  "item_id": "mcp_682d437d90a88191bf88cd03aae0c3e503937d5f622d7a90",
  "output_index": 0
}
```

---

## `response.mcp_call.failed`
Emitted when an MCP tool call has failed.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.mcp_call.failed`.
</details>

**OBJECT `response.mcp_call.failed`**
```json
{
  "type": "response.mcp_call.failed",
  "sequence_number": 1,
  "item_id": "mcp_682d437d90a88191bf88cd03aae0c3e503937d5f622d7a90",
  "output_index": 0
}
```

---

## `response.mcp_call.in_progress`
Emitted when an MCP tool call is in progress.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.mcp_call.in_progress`.
</details>

**OBJECT `response.mcp_call.in_progress`**
```json
{
  "type": "response.mcp_call.in_progress",
  "sequence_number": 1,
  "output_index": 0,
  "item_id": "mcp_682d437d90a88191bf88cd03aae0c3e503937d5f622d7a90"
}
```

---

## `response.mcp_list_tools.completed`
Emitted when the list of available MCP tools has been successfully retrieved.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.mcp_list_tools.completed`.
</details>

**OBJECT `response.mcp_list_tools.completed`**
```json
{
  "type": "response.mcp_list_tools.completed",
  "sequence_number": 1,
  "output_index": 0,
  "item_id": "mcpl_682d4379df088191886b70f4ec39f90403937d5f622d7a90"
}
```

---

## `response.mcp_list_tools.failed`
Emitted when the attempt to list available MCP tools has failed.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.mcp_list_tools.failed`.
</details>

**OBJECT `response.mcp_list_tools.failed`**
```json
{
  "type": "response.mcp_list_tools.failed",
  "sequence_number": 1,
  "output_index": 0,
  "item_id": "mcpl_682d4379df088191886b70f4ec39f90403937d5f622d7a90"
}
```

---

## `response.mcp_list_tools.in_progress`
Emitted when the system is in the process of retrieving the list of available MCP tools.

<details>
<summary>Properties</summary>

-   **`item_id`** `string`
-   **`output_index`** `integer`
-   **`sequence_number`** `integer`
-   **`type`** `string` - Always `response.mcp_list_tools.in_progress`.
</details>

**OBJECT `response.mcp_list_tools.in_progress`**
```json
{
  "type": "response.mcp_list_tools.in_progress",
  "sequence_number": 1,
  "output_index": 0,
  "item_id": "mcpl_682d4379df088191886b70f4ec39f90403937d5f622d7a90"
}
```

