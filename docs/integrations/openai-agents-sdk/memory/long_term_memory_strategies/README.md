# Long-term memory strategies

This document describes the memory strategies used in our OpenAI Agents integration. All strategies operate on **SDK session history** (e.g. `sdk_agent_session_messages` or in-memory `SessionABC` instances), **not** on our durable audit history (`agent_messages`, `agent_run_events`). We always keep the full raw history in our own database.

---

## 1. In-session strategies (current conversation context)

These strategies control **what the model sees inside the active session**.

| Strategy                                 | Implementation / Class                            | Trigger (in this demo)                                         | Effect on session history (SDK view)                                                                                                                                                                                   | What the model sees                                                                                 | Good for                                                                                  | Tradeoffs                                                                                           |
| ---------------------------------------- | ------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **None**                                 | `DefaultSession`                                  | None                                                           | Keeps every message and tool call/result as-is.                                                                                                                                                                        | Full raw history, growing without bound.                                                            | Debugging, short sessions, exact replay.                                                  | Eventually hits context limits on long or tool-heavy conversations.                                 |
| **Trimming**                             | `TrimmingSession`                                 | `max_turns` (user turns); keep `keep_last_n_turns`             | When total user turns ≥ `max_turns`, drops the **oldest** user-anchored turns, keeping only the last `keep_last_n_turns` user turns and their associated assistant/tool messages.                                      | Only the most recent N turns; older turns are completely removed from the session.                  | Simple, cheap way to stay under limits when older detail is expendable.                   | Hard cutoff; early info is gone, and the model cannot directly refer back to it.                    |
| **Summarization**                        | `SummarizingSession` (extends `TrimmingSession`)  | `context_limit` (max user turns) & `keep_last_n_turns`         | When user turns ≥ `context_limit`: split history into **prefix + tail**. Summarize prefix; remove the prefix; insert a shadow user line + assistant summary, then append the unsummarized tail.                        | Tail (last K user turns) plus a synthetic “summary turn” that compresses all earlier context.       | Long, content-rich conversations where older context matters but need not stay verbatim.  | Requires an extra LLM call; quality depends on the summary. Still turn-based, not token-based.      |
| **Compacting**                           | `CompactingSession` / `TrackingCompactingSession` | `trigger.turns` (user turns), `keep` (recent turns to protect) | Once the trigger is exceeded, walks **oldest user turns first** (excluding the last `keep` turns) and replaces tool results (and optionally tool calls) with compact placeholders, preserving tool names and call IDs. | Same conversation structure, but older tool payloads are replaced with “⟦removed: …⟧” placeholders. | Tool-heavy flows where we want to preserve that a tool was used, but not its full output. | Old tool outputs are no longer available; behaviour depends on how informative placeholders are.    |
| **Trimming + summarization interaction** | `SummarizingSession` (inherits trimming logic)    | Internal: trim below limit, summarize once over the limit      | Below `context_limit`, behaves like trimming (keep last N turns). Once over the limit, switches to summarize-then-inject behaviour described above.                                                                    | Smooth transition from “just trimming” to “prefix summarized + last K turns verbatim”.              | Gradual context optimization instead of abrupt growth or deletion.                        | Slightly more complex to reason about; `keep_last_n_turns` must be consistent with `context_limit`. |

**Notes**

* Triggers in this demo are **turn-based** (user message count), not strictly token-based.
* Each session class also keeps internal token **estimates** (chars/4) to compute deltas for visualization (e.g. “context freed this turn”), but those estimates do **not** currently drive the triggers.

---

## 2. Cross-session strategy (future conversations)

This strategy affects **new sessions** by reusing summaries from past sessions.

| Strategy             | Implementation pieces                                                                                | Where it acts                                   | Effect                                                                                                                                                                                                                                                     | When to use                                                                                                        | Tradeoffs                                                                                                                           |
| -------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Memory injection** | `LLMSummarizer` + `_persist_summary_to_disk` + `_load_cross_session_summary` + `_build_instructions` | System prompt / base instructions (not session) | After a summarizing session produces a summary, it is persisted (in this demo: `state/summaries/summary.txt`). On a new run with `memoryInjection` enabled, that summary is loaded and injected into the system instructions as “Cross-session memory: …”. | Multi-session journeys: remembering devices, prior issues, preferences, etc., without re-loading full raw history. | Summary can go stale; we must treat memory as context, not ground truth. Adds steady token overhead to the base prompt per request. |

This is not a `SessionABC` subclass. It is a **prompt-level mechanism**: reuse a summary across sessions instead of replaying the entire prior conversation.

---

## 3. How strategies combine

In this demo, **in-session strategies are mutually exclusive**:

* At most one of:

  * `memoryTrimming`
  * `memorySummarization`
  * `memoryCompacting`
* Plus optionally `memoryInjection` for cross-session memory.

Conceptually:

| Layer         | Choice                                                                                       |
| ------------- | -------------------------------------------------------------------------------------------- |
| In-session    | `DefaultSession` or `TrimmingSession` or `SummarizingSession` or `TrackingCompactingSession` |
| Cross-session | `memoryInjection` off/on (use last summary in system prompt)                                 |

### Recommended defaults (example)

These can be tuned per agent or per conversation type:

* Short/simple flows: **DefaultSession** (no memory management).
* Chatty but low tool usage: **Summarization** with “keep last 3–5 user turns”.
* Tool-heavy flows: **Compacting** with `trigger.turns` tuned to when tool history becomes noisy, `keep` ≈ 2–3 turns.
* Returning-customer / multi-session support: **Summarization + Memory Injection** (persisted summary reused into system prompt).

---

## 4. Conceptual strategy: token-based, model-native compaction

We also consider a **token-based compaction primitive** as a future or model-native strategy. This is not implemented in our current code, but is useful to understand and design towards.

### Idea

Instead of implementing summarization/compaction ourselves, the model (or API) exposes a dedicated **compaction endpoint** that returns a special “compaction item”:

* Input: the current list of items (user messages, assistant messages, tool calls/results, etc.).
* Output: an item of the form:

  ```json
  {
    "type": "compaction",
    "content": "<opaque blob>"
  }
  ```

The opaque content is understood by the model but not necessarily human-readable.

### Trigger

Two layers of triggering:

1. **In our client/app** (explicit):

   * We estimate tokens for the active history using a tokenizer.
   * When total tokens approach some threshold (e.g. 70–80% of the model’s context window), we call the compaction endpoint instead of another normal chat turn.

2. **Inside the model/runtime** (implicit):

   * The model tracks actual token usage.
   * The compaction endpoint is implemented such that the returned compaction item is significantly smaller (in tokens) than the original history, while retaining enough internal state for future reasoning.

### Mechanics

A typical flow:

1. We send the current history items to a **compaction** endpoint.

2. The model returns a **compaction item** with compressed content.

3. We then **drop most or all of the original items** from the active session and keep:

   ```text
   [compaction item, maybe a few most-recent items]
   ```

4. On future normal chat calls, we include that compaction item plus new messages. The model internally decodes the compressed content to “remember” previous context, without us needing to store or send the full raw history.

### Properties

* Trigger is **token-based**, not turn-based.
* Compression is **opaque**:

  * We cannot inspect or directly edit the compressed content.
  * Debugging is harder, since we can’t see what the model “thinks” the history is.
* It is inherently **model-specific**:

  * Tied to whatever format and semantics the model expects for the `compaction` item.

### Relation to our current strategies

Our current implementation:

* Uses **turn-based triggers** (`max_turns`, `context_limit`, `trigger.turns`) for trimming, summarization, and client-side compaction.
* Uses token **estimates** only for telemetry and visualization.
* Keeps compaction and summarization **transparent**:

  * Summaries and placeholders are human-readable.
  * We can log before/after and adjust prompts or thresholds.

A future token-based compaction primitive would complement these:

* We could:

  * Use token-based thresholds to decide when to:

    * Compact tool results (our current `CompactingSession`).
    * Summarize old prefixes (`SummarizingSession`).
  * Or, if/when a model-native compaction endpoint is available, replace some of that logic with a single `compaction` item that the model maintains internally.

For now, strategies 1–3 (None, Trimming, Summarization) and 4 (Compacting) plus cross-session Memory Injection are the **implemented** memory behaviors in our Agents integration; the token-based, model-native compaction strategy in this section is intentionally documented as **conceptual**.


## Package layout

- `agent_service.py` — thin shim entrypoint (keeps `python agent_service.py` working)
- `agent_service/cli.py` — NDJSON loop
- `agent_service/commands.py` — command router
- `agent_service/runtime.py` — agent orchestration (`run_agent`, session selection, etc.)
- `agent_service/tools.py` — mocked function tools + registry
- `agent_service/stores.py` — in-memory stores + cross-session summary persistence
- `agent_service/tool_logging.py` — tool call/event capture for UI
- `agent_service/token_utils.py` — cheap token estimation helpers
- `agent_service/text_extract.py` — extract text from SDK output objects
- `agent_service/sessions/*` — session implementations (default/trimming/summarizing/compacting)
- `agent_service/deps.py` — centralized OpenAI Agents SDK imports with a helpful error message

## Backend wiring in this starter

- Strategies are configurable via API: per-request (`memory_strategy`, `memory_injection`), per-conversation defaults (stored on `agent_conversations`), and per-agent defaults (`AgentSpec.memory_strategy`). Precedence: request > conversation > agent > none.
- SDK session view is modified; durable audit history (`agent_messages`, `agent_run_events`) remains intact.
- Cross-session memory injection stores summaries in `conversation_summaries` and injects them into prompt context when enabled; SDK history is not mutated.
