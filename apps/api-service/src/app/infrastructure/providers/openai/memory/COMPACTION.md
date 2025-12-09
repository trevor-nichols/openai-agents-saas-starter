# Engineering Guide: Conversation Memory & Compression

## Overview

In long-running AI conversations—specifically those involving tools like File Search or Code Interpreter—the context window fills up rapidly. Large tool outputs (CSVs, JSON blobs, file extracts) consume tokens, increase latency, and drive up costs.

The **Conversation Compression** system (implemented internally as `MemoryStrategy.COMPACT`) is a mechanism that surgically removes heavy payloads from the conversation history while retaining the semantic "shape" of the interaction.

## The Problem: Context Bloat

When an Agent runs tools, the conversation history looks like this:

1.  **User:** "Analyze this data."
2.  **Agent (Tool Call):** `code_interpreter.run(code=...)`
3.  **Tool (Output):** `[Huge JSON Blob: 5,000 tokens]`
4.  **Agent (Response):** "I found a trend in the data..."

By turn 10, if we keep sending that 5,000-token JSON blob in `Tool (Output)` back to the LLM, we are paying for it on every subsequent request, even though the Agent already extracted the insight in Turn 4.

## The Solution: Compaction Strategy

The **Compact** strategy applies a "lossy" compression to the history sent to the LLM provider. It works by differentiating between **Recent History** (Hot) and **Older History** (Cold).

### How it works
1.  **Trigger:** The strategy activates when the conversation exceeds a specific turn count (`compact_trigger_turns`) or a token budget (`token_budget`).
2.  **Protection:** It identifies the most recent $N$ turns (configured via `compact_keep`). These are **never** touched.
3.  **Compaction:** For any turn *older* than the protected set, it scans for `tool_call` inputs and `tool_result` outputs.
4.  **Replacement:** It replaces the heavy content with a lightweight placeholder string.

### Data Transformation Example

**Before Compression (Expensive):**
```json
{
  "role": "tool",
  "name": "weather_api",
  "tool_call_id": "call_12345",
  "content": "{ 'temperature': 72, 'humidity': 40, 'forecast': [... 200 lines of JSON ...] }"
}
```

**After Compression (Cheap):**
```json
{
  "role": "tool",
  "name": "weather_api",
  "tool_call_id": "call_12345",
  "content": "⟦removed: tool output for weather_api (call_id=call_12345); reason=context_compaction⟧",
  "compacted": true
}
```

The LLM still sees that a tool was called and returned successfully, maintaining the logical flow of the conversation, but the token load drops to near zero for that step.

---

## API Usage & Configuration

Compression can be configured dynamically per request, persisted to a specific conversation, or baked into the Agent's definition code.

### 1. Per-Request Configuration
The most flexible method is passing the `memory_strategy` object in the `/chat` endpoint.

**Schema (`MemoryStrategyRequest`):**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `mode` | `string` | `none` | Set to `compact` to enable this logic. |
| `compact_keep` | `int` | `2` | The number of recent turns to keep in full fidelity (uncompressed). |
| `compact_trigger_turns` | `int` | `None` | Run compression only after conversation exceeds this many turns. |
| `token_budget` | `int` | `None` | Run compression if estimated tokens exceed this number. |
| `token_soft_budget` | `int` | `None` | Softer threshold; if hit, compaction can still trigger. |
| `context_window_tokens` | `int` | `400000` | Logical context window size used for percentage triggers. |
| `token_remaining_pct` | `float` | `None` | Trigger when remaining budget falls below this fraction (e.g., `0.2` for 20% remaining). If not set and no budgets are provided, a default of 20% is applied. |
| `token_soft_remaining_pct` | `float` | `None` | Optional softer percentage-based threshold. |
| `compact_clear_tool_inputs` | `bool` | `False` | If `true`, also wipes the *input* arguments sent to the tool (aggressive). |
| `compact_exclude_tools` | `list[str]` | `[]` | List of tool names to **never** compress (e.g., `["weather_api"]`). |
| `compact_include_tools` | `list[str]` | `[]` | If provided, **only** these tools will be compressed (takes precedence over exclude). |

**Example Request:**
```json
POST /api/v1/chat
{
  "message": "Analyze the next dataset",
  "agent_type": "data_analyst",
  "memory_strategy": {
    "mode": "compact",
    "compact_keep": 4,
    "token_budget": 8000,
    "compact_clear_tool_inputs": true,
    "compact_include_tools": ["code_interpreter", "file_search"]
  }
}
```

### 2. Conversation Persistence
You can apply a strategy to a conversation ID once, and the server will apply it to all subsequent messages in that thread automatically.

**Endpoint:** `PATCH /api/v1/conversations/{conversation_id}/memory`

```json
{
  "mode": "compact",
  "token_budget": 12000
}
```

### 3. Agent Defaults (Code-Level)
For developers building backend agents, you can define the strategy in the `AgentSpec` so the frontend client doesn't need to know about it.

**File:** `src/app/agents/my_agent/spec.py`
```python
def get_agent_spec() -> AgentSpec:
    return AgentSpec(
        key="data_analyst",
        # ... other config ...
        memory_strategy={
            "mode": "compact",
            "token_budget": 12000,
            "compact_exclude_tools": ["get_user_profile"]
        }
    )
```

**Precedence Order:**
1. Per-Request (Highest)
2. Conversation Persistence
3. Agent Default (Lowest)

---

## Implementation Details

For developers working on the `api-service` codebase, the logic resides in:
`src/app/infrastructure/providers/openai/memory/strategy.py`

### The `StrategySession` Wrapper
We wrap the standard OpenAI SDK session storage. When `add_items` is called (which happens after an Agent run completes), the `StrategySession`:

1.  Fetches current history.
2.  Calculates token estimates (`_estimate_total_tokens`).
3.  Determines if `token_budget` or `compact_trigger_turns` thresholds are met.
4.  Calls `_compact_items()` to rewrite the history list in memory.
5.  Flushes the compacted list to the persistent Session Store.

**Note:** Compaction rewrites the provider session history used for the next LLM call; the durable Postgres `ConversationMessageStore` retains full-fidelity messages for auditing and UI.

### Observability
We emit specific metrics when compaction occurs to help track savings:

*   `memory_compaction_items_total`: Counter of how many tool outputs have been wiped.
*   `memory_tokens_before_after`: Histogram comparing token counts before and after the strategy runs.

## Best Practices

1.  **Code Interpreter:** Always use compaction for Code Interpreter agents. The generated Python code and CSV outputs are massive.
2.  **Tool Filtering:** Use `compact_exclude_tools` for tools that return small, critical state (e.g., `get_user_profile`) that the LLM needs to reference throughout the entire conversation.
3.  **Debugging:** If an Agent seems to "forget" detailed data from 10 turns ago, check if `compact_keep` is set too low.
4.  **Auditing:** Note that this compression affects the **Agent's Memory**. The system `ConversationMessageStore` (Postgres) retains the full-fidelity message history for compliance and UI rendering purposes; this logic only impacts what is sent to the LLM for inference.

5.  **Compact vs. Summarize:** `compact` removes payloads; it does not summarize. Use `summarize` mode if you need semantic summaries instead of placeholders.