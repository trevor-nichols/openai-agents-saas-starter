# Consolidated Gap Analysis (Postmortem) — OpenAI Responses API Streaming Events

**Evaluations:** `docs/trackers/evaluations/openai-responses-api/streaming-events/01-lifecycle.md` through `07-errors.md`  
**Last updated:** 2025-12-16  
**Status:** Implemented (Backend + Frontend).

## Purpose

This document began as a “Source → Contract” audit of OpenAI Responses API streaming events and our end-to-end pipeline:

OpenAI Responses stream → Agents SDK → API service normalization → SSE → Next.js BFF proxy → browser parsing + UI.

As of **2025-12-16**, the redesign has shipped. This file is now a **postmortem + index** so new engineers can quickly understand:

- what the historical gaps were,
- where the implementation lives,
- and how we achieve “professional” transcript ordering (render by `output_index`, update by `item_id`).

## Key streaming identifiers (how to think about `output_index`, `item_id`, `sequence_number`)

These come from the provider Responses streaming schema (see `docs/integrations/openai-responses-api/streaming-events/`).

- **`output_index`**: stable position of an output item within the provider `response.output[]` array. It’s the “transcript row index”.
- **`item_id`**: stable identifier for the specific output item at that index (message id, tool-call id, etc.). It’s the “update key”.
- **`sequence_number`** (provider): monotonically increasing event order number within a single provider stream. It’s the “event emission order”.

**Professional UI rule of thumb**

- Apply **updates** in stream order (arrival order is sufficient for SSE), but **render the transcript** by `output_index`, patching rows by `item_id`.

In our public contract, provider `sequence_number` is surfaced as `provider_sequence_number` (best-effort) and we also emit a server-local, strictly monotonic `event_id`.

## Current state (what’s true now)

- **Public contract (authoritative):** `docs/contracts/public-sse-streaming/v1.md` (`schema="public_sse_v1"`).
- **Backend projection:** `apps/api-service/src/app/api/v1/shared/public_stream_projector/` projects internal `AgentStreamEvent` into public SSE events.
- **Backend endpoints (data-only SSE):**
  - `POST /api/v1/chat/stream` → `apps/api-service/src/app/api/v1/chat/router.py`
  - `POST /api/v1/workflows/{workflow_key}/run-stream` → `apps/api-service/src/app/api/v1/workflows/router.py`
- **Frontend parsing:** `apps/web-app/lib/streams/sseParser.ts` is the single SSE parser (comments + multiline `data:`).
- **Chat transcript ordering:** `apps/web-app/lib/chat/controller/useChatController.ts` inserts assistant rows by `output_index` and updates by `item_id`.
- **Workflows UI:** the “Live events” panel is a debug log (arrival order), and the “Transcript” view is derived from persisted run + conversation state (not the live stream).

## Historical gap inventory (resolved)

| ID | Was priority | Category | Resolution summary | Implementation evidence |
| --- | --- | --- | --- | --- |
| SE-GAP-001 | P0 | SSE protocol | Standardized on data-only SSE + real SSE parsing shared across chat + workflows. | Backend: `apps/api-service/src/app/api/v1/chat/router.py`, `apps/api-service/src/app/api/v1/workflows/router.py`. Frontend: `apps/web-app/lib/streams/sseParser.ts`, `apps/web-app/lib/api/workflows.ts`. |
| SE-GAP-002 | P0 | Security / privacy | Public stream is derived-only (no raw provider payloads); explicit redaction/truncation notices exist. | Contract: `docs/contracts/public-sse-streaming/v1.md`. Backend: `apps/api-service/src/app/api/v1/shared/public_stream_projector/sanitize.py`, `apps/api-service/src/app/api/v1/shared/streaming.py`. |
| SE-GAP-003 | P0 | Error semantics | Provider + server errors translate into `kind="error"` and are terminal. | Backend: `apps/api-service/src/app/api/v1/shared/public_stream_projector/raw.py` (`_project_terminal_errors`). |
| SE-GAP-004 | P1 | Stream semantics | Exactly-one-terminal enforced (`final` or `error`); contract fixtures validate invariants. | Backend: `apps/api-service/src/app/api/v1/shared/public_stream_projector/projector.py`, `apps/api-service/tests/contract/streams/test_stream_goldens.py`. |
| SE-GAP-005 | P1 | Reasoning | Summary-only reasoning is streamed (`reasoning_summary.delta`); final includes `reasoning_summary_text`. | Backend: `apps/api-service/src/app/api/v1/shared/public_stream_projector/raw.py` (`_project_reasoning_summary`). |
| SE-GAP-006 | P1 | Refusal | Refusal is first-class (`refusal.delta` / `refusal.done`) and reflected in `final`. | Backend: `apps/api-service/src/app/api/v1/shared/public_stream_projector/raw.py` (`_project_refusal`). |
| SE-GAP-007 | P2 | Function tools | Tool arguments and outputs are promoted into typed tool events with policy notices. | Backend: `apps/api-service/src/app/api/v1/shared/public_stream_projector/raw.py` (`_project_tool_arguments`), `apps/api-service/src/app/api/v1/shared/streaming.py`. |
| SE-GAP-008 | P2 | MCP tools | MCP status + args + outputs are promoted into typed tool events with policy notices. | Backend: `apps/api-service/src/app/api/v1/shared/public_stream_projector/raw.py`, `apps/api-service/src/app/api/v1/shared/public_stream_projector/run_items.py`. |
| SE-GAP-009 | P2 | Hosted tool fidelity | Hosted-tool lifecycle + code chunks are promoted (web/file search, code interpreter, image generation frames, etc.). | Backend: `apps/api-service/src/app/api/v1/shared/public_stream_projector/raw.py`. |
| SE-GAP-010 | P3 | Robustness | Chunking and citations are supported in the public contract; unused raw families are not forwarded to browsers. | Contract: `docs/contracts/public-sse-streaming/v1.md`. Backend: `apps/api-service/src/app/api/v1/shared/public_stream_projector/raw.py`. |

## Notes for maintainers (debugging ordering)

If you’re debugging “tool card appears below assistant text” or “items appear out of order”:

1. Log these fields per received SSE JSON event: `kind`, `output_index`, `item_id`, `provider_sequence_number`.
2. If a tool event has **lower `output_index`** than the assistant message but renders below it, the UI is still **append-based** and must switch to **insert/update** semantics.
3. If the tool event has **higher `output_index`**, then the model actually placed the tool after the message in `response.output[]` and the UI ordering is correct.

