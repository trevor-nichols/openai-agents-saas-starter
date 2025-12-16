<!-- SECTION: Metadata -->
# Milestone: Resume-Grade SSE Streaming Contract (Responses API + Agents SDK)

_Last updated: 2025-12-15_  
**Status:** Completed (Backend + frontend implemented; tests green)  
**Owner:** (TBD)  
**Domain:** Cross-cutting (API + Web)
**ID / Links:**
- Gap analysis: `docs/trackers/evaluations/openai-responses-api/streaming-events/00-gap-analysis.md`
- Per-topic trackers: `docs/trackers/evaluations/openai-responses-api/streaming-events/01-lifecycle.md` … `07-errors.md`
- Reference (Responses API): `docs/integrations/openai-responses-api/streaming-events/`
- Reference (Agents SDK): `docs/integrations/openai-agents-sdk/agents/streaming_events.md`
- API architecture snapshot: `apps/api-service/SNAPSHOT.md`

---

## Objective

Ship a unified, secure, provider-neutral, strongly typed SSE streaming contract (chat + workflows) aligned with the OpenAI Responses API event model and the OpenAI Agents SDK streaming surface, enabling a professional frontend UX with deterministic contract playback tests.

---

## Decisions (Locked)

### Transport / Framing
- **SSE framing standard:** **Data-only SSE** everywhere (`data: <json>\n\n`), with optional comment heartbeats (`: heartbeat ...\n\n`).
  - Rationale: aligns with typical OpenAI streaming style where the event type lives in JSON, while still using standard SSE framing.
  - Requirement: frontend uses a **robust SSE parser** (not string-prefix hacks) and is shared across chat + workflows.

### Public Payload Policy
- **Public streams are derived-only**:
  - Do **not** send `payload`, `raw_event`, prompts/instructions, tool configs, or other high-risk raw provider blobs to browsers.
  - Emit only productized, typed fields required for UX.
  - Add **correlation fields** (e.g., `conversation_id`, `response_id`, `server_timestamp`, and a trace/request id if available) to preserve debuggability without leaking content.

### Terminal Semantics
- Add a first-class **terminal event**: `kind="final"` with `status`.
  - Invariant: exactly **one terminal** event per stream.
  - Terminal event shape includes final output and summary metadata (usage, attachments, refusal, etc.) as appropriate.
- **`final.status` enum:** `completed | failed | incomplete | refused | cancelled`

### Reasoning
- **Summary-only** reasoning in public streams:
  - Stream only `response.reasoning_summary_*` / `response.reasoning_summary_text.*` derived fields.
  - Treat `response.reasoning_text.*` as **server-only** (never forwarded to browsers).
  - Include `*.done` fallbacks so UI is robust if deltas are sparse.

### Refusal
- Refusal is a **first-class** UX concept (not an error):
  - Stream refusal deltas and a final refusal payload.
  - Terminal `final.status` reflects refusal outcome as a distinct state.

### Tool Arguments Visibility
- Function tool and MCP tool **arguments must be visible in the UI**.
  - If redacted/truncated, the event must carry a **redaction indicator** and a short explanation suitable for display.
  - Hosted tools (web/file/code/image) should have **predictable typed payloads** per the reference docs in `docs/integrations/openai-responses-api/streaming-events/04-builtin-tools.md`.
- **Tool args representation:** include both `arguments_text` (lossless string) and `arguments_json` (best-effort parsed) for function + MCP tools.

### Errors
- Public error events always use `kind="error"` with a structured payload:
  - `{ code?: string, message: string, source: "provider" | "server", is_retryable: boolean }`

---

## Limits (Proposed defaults — pending final sign-off)

These are **transport guardrails**, not “model output” limits.

They exist because SSE is plaintext and many runtime/proxy/browser stacks will:
- buffer large frames in memory before the `\n\n` delimiter is found,
- time out or become unstable on very large single events,
- degrade UX on high-frequency huge payloads.

Design goal: **unbounded semantics, bounded frames**. Large payloads are streamed via **chunk sequences** so we don’t need small caps on what agents can do.

When a guardrail is applied (chunking, truncation, redaction), the event must include an explicit indicator so the UI can render “(chunked) / (truncated) / (redacted)” intentionally.

### Per-event
- **Max serialized event size:** 1 MiB (hard cap).
  - If an event would exceed this, it must be **chunked** into multiple events.
  - Never drop the terminal event; terminal may also be chunked where needed.

### Per-stream (circuit breaker)
- **Max serialized bytes per stream:** 128 MiB (hard cap, configurable).
  - This is an abuse/OOM circuit breaker, not expected to trigger in normal usage.

### Chunking protocol (for any large field)
- Chunk sequence events include:
  - `stream_id` (stable per response/run), `entity_id` (tool_call_id / message_id), `field` (e.g., `partial_image_b64`),
  - `chunk_index` (0-based), `chunk_count` (optional), and `data` (string chunk).
- The UI reassembles chunks for display. If `chunk_count` is unknown, completion is signaled by a dedicated `*.chunks_done` event.

### Image generation (streaming enabled)
- **Partial images:** stream as base64 via chunk sequences (preferred) so previews work without giant frames.
- **Final images:** always “store + reference” via attachments / presigned URLs, but may also be streamed as base64 chunks when explicitly enabled for UX parity.


---

## Definition of Done

- Chat and workflow streaming endpoints emit **the same SSE framing** and the **same public event union**.
- Public stream contract is a **discriminated union** (strong types; no “wide optional bag” model).
- Public streams are **derived-only** (no prompts/instructions/tool configs/raw blobs).
- Tool timeline supports:
  - Hosted tools with typed payloads and full status fidelity (`in_progress` vs `searching` where applicable).
  - Function/MCP tools with argument deltas + final arguments (with redaction markers).
- Reasoning summary panel works end-to-end (fixtures + UI render).
- Refusal renders end-to-end (fixtures + UI render).
- Errors are consistent and always surface as a terminal UI-visible error event when applicable.
- Deterministic playback tests cover:
  - terminal invariants (exactly one terminal)
  - provider `error` → UI error
  - `failed` / `incomplete` / refusal terminal paths
  - hosted tools + function tools + (optional) MCP
- Tooling is green:
  - Backend: `cd apps/api-service && hatch run lint && hatch run typecheck && hatch run pytest`
  - Frontend: `cd apps/web-app && pnpm lint && pnpm type-check && pnpm test` (or repo-standard commands)
- OpenAPI + SDK regeneration performed for any schema changes (per repo rules).
- Trackers updated (gap analysis marked addressed; links to PRs/commits).

---

## Scope

### In Scope
- Redesign streaming schemas for the public contract (chat + workflows).
- Unify SSE framing and parsing (shared implementation).
- Implement a strict public streaming payload policy (derived-only) with explicit redaction/truncation.
- Improve hosted tool fidelity (status + code-interpreter `*.done`, etc.).
- Add streaming coverage for: error, final states, refusal, reasoning summaries, function tools, MCP tools (optional).

### Out of Scope
- Non-streaming responses contract changes (unless required to keep contracts coherent).
- Product-level UI redesign beyond what’s required to render the new stream contract cleanly.
- Backwards compatibility shims.

---

## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Public contract defined + implemented (see `docs/contracts/public-sse-streaming/v1.md`). Web app consumes `public_sse_v1` end-to-end. |
| Implementation | ✅ | API service emits **data-only SSE** + heartbeats + derived-only projection; Next.js BFF is a pass-through; web app uses a robust shared SSE parser + typed adapters. |
| Tests & QA | ✅ | Deterministic contract playback tests cover both backend and web app: tools (hosted/function/MCP), refusal, provider errors, reasoning summaries, and terminal invariants (`exactly one terminal event`). |
| Docs & runbooks | ✅ | Authoritative public contract doc + example NDJSON fixtures exist under `docs/contracts/public-sse-streaming/`. |

### Review findings (2025-12-15)

**Backend implementation (public contract + projection)**
- Contract schema: `apps/api-service/src/app/api/v1/shared/streaming.py` (`PublicSseEvent`, `public_sse_v1`)
- Projection: `apps/api-service/src/app/api/v1/shared/public_stream_projector.py` (`PublicStreamProjector`)
- SSE endpoints (data-only framing + optional heartbeat comments):
  - `POST /api/v1/chat/stream` (`apps/api-service/src/app/api/v1/chat/router.py`)
  - `POST /api/v1/workflows/{workflow_key}/run-stream` (`apps/api-service/src/app/api/v1/workflows/router.py`)

**Key contract capabilities implemented**
- Explicit terminal events: `kind="final"` / `kind="error"` (exactly one per stream)
- Reasoning: **summary-only** (`reasoning_summary.delta`), never forwards `response.reasoning_text.*`
- Refusal: `refusal.delta` / `refusal.done` and terminal `final.status="refused"`
- Tools: typed tool state (`tool.status`) for hosted tools + function + MCP, plus tool code deltas/done for code interpreter
- Large payload safety: chunking for image partial frames + redaction/truncation notices for tool args/outputs

**Quality gates (backend)**
- `cd apps/api-service && hatch run lint` ✅
- `cd apps/api-service && hatch run typecheck` ✅
- `cd apps/api-service && hatch run test` ✅ (runs `pytest -m 'not smoke and not integration'`)
  - Note: running full `hatch run pytest` includes `smoke` (expects a running server) and some `integration` tests (Docker/external deps).

**Frontend implementation (web app)**
- Shared SSE parser: `apps/web-app/lib/streams/sseParser.ts` (comments + multi-line `data:` + CRLF)
- Streaming consumers: `apps/web-app/lib/api/chat.ts` and `apps/web-app/lib/api/workflows.ts`
- Chat adapter/controller updated to `public_sse_v1`: `apps/web-app/lib/chat/adapters/chatStreamAdapter.ts` + `apps/web-app/lib/chat/controller/useChatController.ts`
- Workflow stream log renderer updated: `apps/web-app/features/workflows/components/WorkflowStreamLog.tsx`
- Generated client regeneration performed: `apps/api-service/.artifacts/openapi-fixtures.json` → `apps/web-app/lib/api/client/types.gen.ts`

**Quality gates (frontend)**
- `cd apps/web-app && pnpm lint` ✅
- `cd apps/web-app && pnpm type-check` ✅
- `cd apps/web-app && pnpm test` ✅

**Important correctness fix applied during review**
- Avoided prematurely closing the upstream async generator after emitting the terminal SSE event. The chat/workflow routers now stop emitting to the client after terminal while continuing to drain upstream so persistence/finalization completes.
- Fixed workflow stream termination: per-step provider “terminal” events are no longer treated as stream terminal; workflows now emit exactly one terminal `final/error` event at the end of the workflow run.

---

## Architecture / Design Snapshot

### Target layering (clean architecture)

1. **Provider stream (OpenAI Responses via Agents SDK)** → raw events
2. **Domain normalization (provider adapter)** → internal `AgentStreamEvent` (may keep rich/raw for server-only processing)
3. **Public contract projection** (new) → `PublicStreamingEvent` discriminated union + redaction/truncation
4. **SSE encoder** (shared) → `data: <json>\n\n` (+ comment heartbeats)
5. **Next.js BFF pass-through** (no transformation)
6. **Frontend SSE parser** (shared) → typed events
7. **UI adapter/controller** → UX state (text, reasoning summary, refusal, tools, attachments, terminal)

### Key contract principles
- Public event union is **provider-neutral** (no OpenAI raw event blobs).
- Sensitive content is handled by an explicit **stream redaction policy**.
- Tools are modeled as typed **state machines** (status progression + inputs/outputs).
- Terminal semantics are explicit and testable (one terminal event).

---

## Workstreams & Tasks

### Workstream A — Public Streaming Contract (Schemas + Policy)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Design | Define `PublicStreamingEvent` discriminated union + shared metadata | TBD | ✅ |
| A2 | Design | Define tool payload unions (hosted + function + MCP) + redaction markers | TBD | ✅ |
| A3 | Design | Define terminal `final` payload + status enum + invariants | TBD | ✅ |
| A4 | Policy | Write “derived-only” redaction/truncation policy spec (limits + allowlists) | TBD | ✅ |

### Workstream B — Backend Implementation (API Service)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | SSE | Add shared SSE encoder used by chat + workflows (data-only + heartbeats) | TBD | ✅ |
| B2 | Projection | Implement `AgentStreamEvent` → `PublicStreamingEvent` projection (derived-only) | TBD | ✅ |
| B3 | Tools | Promote missing hosted-tool fidelity (`web_search.searching`, `code_interpreter_call_code.done`, etc.) | TBD | ✅ |
| B4 | Tools | Implement function + MCP args aggregation/deltas + redaction | TBD | ✅ |
| B5 | Errors | Normalize provider `type="error"` + failure states into terminal error semantics | TBD | ✅ |
| B6 | Terminal | Emit `kind="final"` terminal event (exactly once) | TBD | ✅ |

### Workstream C — Frontend Implementation (Web App)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | SSE | Implement shared SSE parser (supports comments + multi-line data) | TBD | ✅ |
| C2 | API | Replace chat/workflow stream readers to use the shared parser | TBD | ✅ |
| C3 | UX | Update chat controller/adapter to new event union (text/reasoning/refusal/tools/final) | TBD | ✅ |
| C4 | UX | Update workflow stream log renderer to new event union | TBD | ✅ |

### Workstream D — Tests, Fixtures, and Validation

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Backend | Contract tests for terminal invariants + error/refusal/reasoning/tool args | TBD | ✅ |
| D2 | Manual | Add manual tests to record fixtures: refusal, reasoning summary, function args, (optional) MCP | TBD | ✅ |
| D3 | Frontend | Unit tests for SSE parser + adapters (error/refusal/reasoning/tools) | TBD | ✅ |

### Workstream E — Documentation

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| E1 | Docs | Add “Public SSE Contract” doc (authoritative) + examples | TBD | ✅ |
| E2 | Trackers | Update gap analysis + per-topic trackers with resolutions + links | TBD | ✅ |

---

## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Contract alignment | Lock event union + terminal semantics + redaction policy | A1–A4 done | ✅ | 2025-12-15 |
| P1 – Backend projection | Backend emits the new public contract for chat + workflows | B1–B6 done | ✅ | 2025-12-15 |
| P2 – Frontend migration | Web app fully consumes new contract | C1–C4 done | ✅ | 2025-12-15 |
| P3 – Fixtures + tests | Deterministic playback coverage and new fixtures recorded | D1–D3 done | ✅ | 2025-12-15 |
| P4 – Polish + docs | Trackers closed; docs finalized; consistency sweep | E1–E2 done | ✅ | 2025-12-15 |

---

## Dependencies

- OpenAPI + SDK regeneration rules (must follow repo guidance before editing `apps/web-app/lib/api/client/*`):
  - Export OpenAPI fixtures → regenerate HeyAPI client → then update web-app code.
- Manual tests require live OpenAI credentials/tooling; keep them opt-in.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Derived-only reduces browser-side debuggability | Med | Add correlation IDs + server-side tracing/log pointers; optionally add a dev-only debug stream later. |
| Tool args contain secrets/PII | High | Redaction allowlists + truncation limits + explicit “redacted” UX markers. |
| Large payloads (images/search results) blow up SSE | High | Store-and-reference for binaries; strict size caps for tool outputs. |
| Schema unions complicate OpenAPI/client generation | Med | Use discriminated unions with stable `kind`; keep union small; add fixture-backed tests. |

---

## Validation / QA Plan

- Backend:
  - `cd apps/api-service && hatch run lint`
  - `cd apps/api-service && hatch run typecheck`
  - `cd apps/api-service && hatch run test` (contract + unit; excludes smoke/integration by default)
  - Optional (requires deps):
    - `cd apps/api-service && hatch run pytest -m smoke` (expects a running server)
    - `cd apps/api-service && hatch run pytest -m integration` (Docker/external deps)
- Frontend:
  - `cd apps/web-app && pnpm lint`
  - `cd apps/web-app && pnpm type-check`
  - `cd apps/web-app && pnpm test` (or repo-standard)
- Manual (opt-in) fixture recording:
  - Extend `apps/api-service/tests/manual/*` and record NDJSON fixtures for new event kinds.

---

## Rollout / Ops Notes

- No backwards compatibility targets.
- Streaming endpoints are updated atomically across API service + web app.
- Prefer a short-lived feature branch for the refactor; merge once tests/fixtures are green.

---

## Open Decisions (Need confirmation)

Closed (implemented in `public_sse_v1`):
- `final.status` enum: `completed | failed | incomplete | refused | cancelled`
- Public error shape: `kind="error"` with `{ code?, message, source, is_retryable }`
- Tool args representation: `arguments_text` + best-effort `arguments_json` with explicit redaction/truncation notices

Still open / worth tightening:
- Global per-event size enforcement (we chunk image partial frames; we don’t yet enforce a strict “max serialized event size” across all kinds).
- Redaction allowlists per tool name (current behavior is “sensitive-key substring” redaction + truncation).

---

## Changelog

- 2025-12-15 — Created milestone and locked initial decisions based on the streaming gap analysis.
- 2025-12-15 — Review update: backend `public_sse_v1` contract implemented + documented; backend lint/typecheck/tests green; noted remaining frontend migration + expanded fixture coverage (reasoning/MCP) and optional smoke/integration runs.
- 2025-12-15 — Web app migration complete: robust SSE parser + typed adapters/controllers + workflow log renderer; frontend lint/type-check/tests green.
