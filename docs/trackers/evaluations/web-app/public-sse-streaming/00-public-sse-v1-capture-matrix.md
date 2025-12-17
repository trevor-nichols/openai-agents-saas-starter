# Web App SSE Capture Matrix — `public_sse_v1` (Chat vs Workflows)

**Last updated:** 2025-12-17  
**Scope:** browser-facing capture/surfacing of the **public SSE contract** (`schema="public_sse_v1"`), for both chat streaming and workflow run streaming.  
**Contract (authoritative):** `docs/contracts/public-sse-streaming/v1.md`  
**Generated TS types:** `apps/web-app/lib/api/client/types.gen.ts` (`StreamingChatEvent`, `StreamingWorkflowEvent`)

## Definitions

- **Contract-supported:** the event `kind` exists in `public_sse_v1` and therefore can appear on the wire for *either* stream.
- **Captured (chat):** the event affects chat UI state via `consumeChatStream` + the chat controller turn reducer pipeline.
- **Captured (workflows):** the event is accumulated in `useWorkflowRunStream` and affects at least one workflow view model.
- **Surfaced:** the event is visible in the default UI (not only logged / ignored).
  - Workflows have two “surfaces”: the **Live Stream** transcript and the **Debug events** log.

## Capture matrix (by `PublicSseEvent.kind`)

Legend:
- ✅ yes
- 🟨 partial / indirect
- ⛔ no (ignored / not handled)

| `kind` | Contract-supported | What it does | Chat: captured | Chat: surfaced | Workflows: captured | Workflows: live stream surfaced | Workflows: debug log surfaced | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `lifecycle` | ✅ | High-level response/run status (`queued`, `in_progress`, `completed`, `failed`, `incomplete`, `cancelled`) + optional `reason`. `response.created` is collapsed into `in_progress`; terminal UX is usually driven by `final`/`error`. | ✅ | 🟨 | ✅ | ⛔ | ✅ | Workflows surface lifecycle indirectly via `streamStatus`, but the live transcript builder ignores it. |
| `memory.checkpoint` | ✅ | UX marker emitted when the server applies a memory strategy mutation during a run (internal lifecycle event `memory_compaction`). Indicates the memory strategy used (`compact|summarize|trim`) and optional trigger/telemetry (e.g. token budgets, turns, counts). Must not retroactively change prior messages; it explains why the model may lose context. | ✅ | ✅ | ✅ | ⛔ | ✅ | Workflows don’t project memory checkpoints into the live transcript today. |
| `agent.updated` | ✅ | Active-agent change signal (handoff/routing). Includes `from_agent`, `to_agent`, optional `handoff_index`. This is the public replacement for raw “handoff” run-item events. | ⛔ | ⛔ | ✅ | ⛔ | ✅ | Chat currently infers “agent switch” from `event.agent` changes, not `kind="agent.updated"`. |
| `output_item.added` | ✅ | Insert signal for a single provider output item at `output_index` (keyed by stable `item_id`). `item_type` can represent **messages and tool calls** (e.g. `message`, `function_call`, `web_search_call`, `file_search_call`, `code_interpreter_call`, `image_generation_call`, `mcp_call`, etc.). **Ordering rule:** render the transcript list by `output_index` and update-in-place by `item_id` (do not append by arrival time). | ✅ | 🟨 | ✅ | ✅ | ✅ | Chat uses this for ordering/placeholders; not directly rendered as a discrete UI element. |
| `output_item.done` | ✅ | Completion signal for a single output item (same identity as `output_item.added`). Marks that item “done” and often coincides with tool call details becoming complete (args/results/status). **Ordering rule:** updates still apply by `item_id`, but the rendered position stays at its `output_index` slot. | ✅ | 🟨 | ✅ | ✅ | ✅ | Same as `output_item.added` (mainly state for ordering + “done” semantics). |
| `message.delta` | ✅ | Streaming assistant-visible message text tokens for a specific message output item (`item_id`, `output_index`, `content_index`). This is the main “typing” signal; apply as in-place updates to the message at that `output_index` slot. | ✅ | ✅ | ✅ | ✅ | ✅ | Primary transcript text streaming. |
| `message.citation` | ✅ | Citation annotation for a specific span of assistant text (via `start_index`/`end_index`) using `url_citation`, `file_citation`, or `container_file_citation`. Used for web search result attribution and also for file-search / container-file references; web-search citations may arrive after tool completion and trigger a follow-up `tool.status` refresh with updated `sources`. | ✅ | ✅ | ✅ | ⛔ | ✅ | Workflow live transcript ignores citations; debug log shows them. |
| `reasoning_summary.delta` | ✅ | Append-only streamed reasoning **summary** text (browser-safe), keyed by `summary_index`. Typically follows `reasoning_summary.part.added`; a `response.reasoning_summary_text.done` may produce a final “suffix delta” if it contains more than the accumulated deltas. Full `reasoning_summary_text` is also echoed in the terminal `final` payload. | ✅ | ✅ | ✅ | ✅ | ✅ | Chat surfaces via `ReasoningPanel`; workflows show in Live Stream header collapsible. |
| `reasoning_summary.part.added` | ✅ | Chunk boundary: indicates a new reasoning-summary “part” began (keyed by `summary_index`, `part_type="summary_text"`). Intended for UX like “one bullet per chunk”: create a placeholder on `part.added`, then stream text via `reasoning_summary.delta`. | ⛔ | ⛔ | ✅ | ⛔ | ✅ | Not handled by chat or workflow live transcript. |
| `reasoning_summary.part.done` | ✅ | Chunk boundary: indicates the reasoning-summary “part” finished; includes the final full text for that `summary_index` / `part_type`. Useful to mark the chunk complete (and/or reconcile if deltas were missing). | ⛔ | ⛔ | ✅ | ⛔ | ✅ | Not handled by chat or workflow live transcript. |
| `refusal.delta` | ✅ | Provider/model refusal text (maps from raw `response.refusal.delta`), streamed as incremental deltas for a specific message/content part (`item_id`, `output_index`, `content_index`). This is *not* our app guardrails; guardrail emissions are separate internal events and aren’t part of `public_sse_v1`. | ✅ | ✅ | ✅ | ✅ | ✅ | Chat treats refusal as an alternate text channel; workflows render refusal blocks. |
| `refusal.done` | ✅ | Provider/model refusal text completion (maps from raw `response.refusal.done`). Carries the authoritative final `refusal_text` and is echoed into the terminal `final.refusal_text` with `final.status="refused"`. | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `tool.status` | ✅ | Tool lifecycle + metadata. `tool` is a discriminated union by `tool_type`. Hosted tools surface their “results” here (`web_search.sources`, `file_search.results`, `code_interpreter.container_id/mode`, `image_generation` metadata). Function/MCP tools surface execution state (`in_progress|completed|failed`, MCP adds `awaiting_approval`) and may include `arguments_*` / `output` fields when known. | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `tool.arguments.delta` | ✅ | Best-effort streaming tool **input arguments** for `tool_type="function"` and `tool_type="mcp"` (sanitized; not guaranteed 1:1 with provider deltas). Useful for showing “tool is being prepared” before final args are available. | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `tool.arguments.done` | ✅ | Authoritative final tool **input arguments** for `tool_type="function"` and `tool_type="mcp"` (`arguments_text` + best-effort parsed `arguments_json`). | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `tool.code.delta` | ✅ | Streaming code snippet text for `tool_type="code_interpreter"` tool calls (incremental “what code is running” UX). | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `tool.code.done` | ✅ | Final complete code string for `tool_type="code_interpreter"` tool calls (authoritative code). | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `tool.output` | ✅ | Structured tool outputs. In the current backend projection we emit `tool.output` for **function and MCP** tools (sanitized), while hosted tools typically expose outputs via `tool.status` (and `chunk.*` for large fields like partial images). | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `tool.approval` | ✅ | Approval decision record for an **MCP** tool call only (approved/denied + optional reason). Distinct from execution lifecycle: the request/wait state is reflected via `tool.status` with `tool_type="mcp"` and `status="awaiting_approval"`. | ⛔ | ⛔ | ✅ | ⛔ | ✅ | Workflows only show approvals in debug; chat ignores approvals entirely. |
| `chunk.delta` | ✅ | Chunk streaming for large fields (generic mechanism). **Currently used in the web app only for image generation partials**: accumulate `target.entity_kind="tool_call"` + `target.field="partial_image_b64"` (+ `encoding="base64"`) until `chunk.done`, then assemble into partial image frames for the image-generation tool UI. | ✅ | 🟨 | ✅ | ✅ | ✅ | Used for chunked payloads (e.g. partial image frames). Chat/workflows surface results via tool UI, not as raw chunk events. |
| `chunk.done` | ✅ | Terminator for a chunk target. **Currently used in the web app only for image generation partials** (signals that the accumulated `partial_image_b64` chunks for a given `part_index` can be decoded/assembled into a frame). | ✅ | 🟨 | ✅ | ✅ | ✅ | |
| `error` | ✅ | Terminal event for failures where a structured `final` summary cannot be produced. Includes normalized error payload (`code?`, `message`, `source=provider|server`, `is_retryable`). After `error`, the stream ends and consumers should stop processing further events. | ✅ | ✅ | ✅ | ⛔ | ✅ | Workflows live transcript intentionally drops terminal events; status banner reflects error. |
| `final` | ✅ | Terminal event for all non-exceptional endings (including `failed`, `incomplete`, `refused`, `cancelled`). Carries the final run summary (`status`, `response_text`, `structured_output`, `reasoning_summary_text`, `refusal_text`, `attachments`, `usage`). After `final`, the stream ends and consumers should stop processing further events. | ✅ | ✅ | ✅ | ⛔ | ✅ | Workflows live transcript intentionally drops terminal events; status banner reflects completion. |

## Evidence pointers (current implementation)

- **SSE parsing (shared):** `apps/web-app/lib/streams/sseParser.ts`
- **Chat stream transport:** `apps/web-app/lib/api/chat.ts`
- **Chat capture/reducer:** `apps/web-app/lib/chat/adapters/chatStream/consumeChatStream.ts`
- **Workflow stream transport:** `apps/web-app/lib/api/workflows.ts`
- **Workflow capture/hook:** `apps/web-app/features/workflows/hooks/useWorkflowRunStream.ts`
- **Workflow live transcript reducer:** `apps/web-app/lib/workflows/liveStreamTranscript.ts`
- **Workflow debug log:** `apps/web-app/features/workflows/components/runs/streaming/WorkflowStreamLog.tsx`

## Known gaps (candidates for parity decisions)

- **Chat ignores**: `agent.updated`, `tool.approval`, `reasoning_summary.part.*`.
- **Workflow live transcript ignores**: `lifecycle`, `memory.checkpoint`, `agent.updated`, `message.citation`, `reasoning_summary.part.*`, `tool.approval`, terminal events (`final`/`error`).
