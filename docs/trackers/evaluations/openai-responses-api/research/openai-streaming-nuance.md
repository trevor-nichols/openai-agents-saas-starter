### What developers are reporting (very similar symptoms)

* **Agents SDK stream ordering can be “late” / buffered**, which makes tool UI show up after message UI even when the model/tool happened earlier.

  * In `openai-agents-python`, one issue shows `run_item_stream_event` events (tool-called / tool-output / message-output) being emitted in an order that breaks “chronological UI,” and explicitly calls out UI impacts. ([GitHub][1])
  * Another issue: `Runner.run_streamed()` **buffers `tool_call_item` events** and only emits them when the tool actually starts executing, which delays real-time tool cards in UIs. ([GitHub][2])
  * A later bug report says some events (e.g., reasoning/tool lifecycle) are emitted **out of spec order**, and explicitly notes it causes UIs to “show the wrong thing.” ([GitHub][3])

* **Responses API streaming nuance:** for tool calls, libraries sometimes expect tool args “up front,” but in practice the **complete tool arguments may only be present at `response.output_item.done`**, which can make a tool card appear “late” if your UI waits for full args before rendering. This exact mismatch is documented in a LangChain JS issue with a sample stream. ([GitHub][4])

* **OpenAI’s own streaming schema is designed for “insert/update,” not “append.”** Each event includes `output_index`, `item_id`, and `sequence_number`. If you append components as events arrive, you can easily mis-order tool calls vs assistant text. ([OpenAI Platform][5])

* Also worth noting: some devs see the model return both a **message + function_call** and recommend ignoring the “message” if a tool call is present (because it’s often just pre-tool chatter that shouldn’t render like a final assistant bubble). ([OpenAI Community][6])

---

### The fix pattern that prevents “tool cards show below the answer”

If you want the UI to be *chronological* the way the model intended, don’t render by arrival time.

**Render by `output_index` (and update by `item_id`)**:

1. On `response.output_item.added`, **create a placeholder slot at `output_index` immediately** (even if you don’t have args/results yet).
2. As deltas arrive (`response.function_call_arguments.delta`, tool lifecycle events, `response.output_text.delta`), **mutate that existing slot**, don’t append a new row.
3. When `response.output_item.done` arrives, finalize (and if it’s a function_call, parse the now-complete args). ([OpenAI Platform][5])

This alone usually fixes the “tool happened first but appears below” problem — because when a late tool event arrives with a **lower output_index**, you insert it above the assistant text instead of appending it at the bottom.

---

For the **Responses API**, the “professional” way to build a stable chat transcript is:

* **Position items by `output_index`** (that’s the index into `response.output[]`)
* **Patch/update items by `item_id`** (and `content_index` when you’re inside message content)
* **Do not treat “event arrival order” as your render order**

OpenAI’s own docs basically nudge you this way: tool/function-call streaming is described as `response.output_item.added` + a series of `response.function_call_arguments.delta` events keyed by `output_index` + `item_id`, and their accumulation example keys tool calls by `output_index`. ([OpenAI Platform][7])

Likewise for text streaming, `response.output_text.delta` includes `item_id` + `output_index` (+ `content_index`), which is exactly the “patch this specific thing in place” model. ([OpenAI Platform][8])

### The nuance

You still **apply updates in stream order** (events have `sequence_number`), but you **render the list** by `output_index`. ([OpenAI Platform][8])

If you want “chronological activity” (tool started / tool finished / etc.), that’s a different view — use `sequence_number` there. But for the main chat transcript, ordering by `output_index` + patching by `item_id` is the standard approach.

---

### Trouble Shooting

Log just these per SSE event: `type`, `output_index`, `item_id`, `sequence_number`.

* If the tool’s `output_index` is **less than** the assistant message’s `output_index`, but your UI shows it below → **your renderer is append-based** (needs insertion by output_index).
* If the tool’s `output_index` is **greater than** the assistant message’s `output_index` → the model actually emitted assistant text first (can happen with multi-item outputs), and your UI is technically correct.

[1]: https://github.com/openai/openai-agents-python/issues/583 "Ordering of events in Runner.run_streamed is incorrect · Issue #583 · openai/openai-agents-python · GitHub"
[2]: https://github.com/openai/openai-agents-python/issues/1282 "Bug: `run_streamed` Buffers `tool_call_item` Events, Delaying Real-Time Feedback · Issue #1282 · openai/openai-agents-python · GitHub"
[3]: https://github.com/openai/openai-agents-python/issues/1767 "ReasoningItem of RunStreamEvents are getting emitted out of order · Issue #1767 · openai/openai-agents-python · GitHub"
[4]: https://github.com/langchain-ai/langchainjs/issues/8049 "OpenAI: When using streaming with responses API, tool call arguments are parsed incorrectly. · Issue #8049 · langchain-ai/langchainjs · GitHub"
[5]: https://platform.openai.com/docs/api-reference/responses-streaming "Streaming events | OpenAI API Reference"
[6]: https://community.openai.com/t/responses-api-returns-message-function-call/1293055?utm_source=chatgpt.com "Responses API returns message + function_call"
[7]: https://platform.openai.com/docs/guides/function-calling "Function calling | OpenAI API"
[8]: https://platform.openai.com/docs/api-reference/responses-streaming "Streaming events | OpenAI API Reference"