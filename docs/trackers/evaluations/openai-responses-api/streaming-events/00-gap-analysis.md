# Consolidated Gap Analysis — OpenAI Responses API Streaming Events

**Evaluations:** `docs/trackers/evaluations/openai-responses-api/streaming-events/01-lifecycle.md` through `07-errors.md`  
**Last updated:** 2025-12-15  
**Status:** Implemented (Backend + Frontend).

## Purpose

This document consolidates all gaps identified during the “Source → Contract” audit of OpenAI Responses API streaming events and our end-to-end pipeline:

OpenAI Responses stream → Agents SDK → API service normalization → SSE → Next.js BFF proxy → browser parsing + UI.

It is intended to drive a professional, intentional redesign (no backwards-compat constraints).

## Guiding principles (resume-grade posture)

1. **Single source of truth for SSE contract**: one framing + one parser strategy across endpoints.
2. **Security-first payload policy**: never stream prompts/hidden instructions or sensitive tool payloads to browsers by default.
3. **Provider-neutral, typed surface**: UI consumes stable typed fields; raw fidelity is optional and sanitized.
4. **Explicit terminal semantics**: every stream ends with an unambiguous terminal event.
5. **Deterministic coverage**: contract playback tests validate invariants; manual tests record new fixtures for real-tool flows.

## Gap inventory (prioritized)

| ID | Priority | Category | Summary | Primary evidence |
| --- | --- | --- | --- | --- |
| SE-GAP-001 | P0 | SSE protocol | Workflow SSE framing is incompatible with the current frontend parser (likely drops all workflow events). | `01-lifecycle.md` “SSE framing consistency”; `07-errors.md` “Workflow stream framing”; `apps/web-app/lib/api/workflows.ts` vs `apps/api-service/src/app/api/v1/workflows/router.py` |
| SE-GAP-002 | P0 | Security / privacy | Raw payloads forwarded to browsers can leak prompts/tool configs and sensitive tool outputs (file excerpts, large base64 frames). No explicit redaction/truncation policy. | `01-lifecycle.md` “Redaction risk”; `02-output-content.md` “Payload size/PII”; `04-builtin-tools.md` “Payload size + privacy” |
| SE-GAP-003 | P0 | Error semantics | OpenAI `type="error"` currently arrives as `raw_type="error"` but is not translated into UI-visible `kind="error"` and is not terminal; error channel semantics are inconsistent. | `07-errors.md` |
| SE-GAP-004 | P1 | Stream semantics | Terminal semantics for `response.failed` / `response.incomplete` / `response.queued` are not explicitly tested; stream can end ambiguously (or “complete” after an error). | `01-lifecycle.md`, `07-errors.md` |
| SE-GAP-005 | P1 | Reasoning | We conflate `reasoning_text` vs `reasoning_summary_text` into one field, do not handle `*.done` fallbacks, and have no fixtures covering reasoning events; also potential policy risk streaming full reasoning. | `06-reasoning.md` |
| SE-GAP-006 | P1 | Refusal | `response.refusal.*` is passthrough-only; UI won’t render refusal text; no tests/fixtures. | `02-output-content.md` |
| SE-GAP-007 | P2 | Function tools | Function-call delta events are passthrough-only (no aggregation/typed promotion); no fixtures; unclear whether SDK emits `custom_tool_call_input.*` vs `function_call_arguments.*` for our tools. | `03-function-calls.md` |
| SE-GAP-008 | P2 | MCP tools | MCP is config-ready but streaming is raw-only; no typed tool surface or fixtures; no “hello world” manual test. | `05-mcp-tools.md` |
| SE-GAP-009 | P2 | Hosted tool fidelity | A few hosted-tool details are lossy or incomplete (`code_interpreter_call_code.done` not promoted; status fidelity collapsed for web/file search). | `04-builtin-tools.md` |
| SE-GAP-010 | P3 | Robustness / future-proofing | `content_part.*` and non-citation annotations are forwarded but unused; `output_text.done` not used as fallback. | `02-output-content.md` |

## Resolution (backend)

These gaps are addressed by the `public_sse_v1` contract and projection:

- **Public contract (authoritative):** `docs/contracts/public-sse-streaming/v1.md`
- **Projection (derived-only):** `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
- **Schemas:** `apps/api-service/src/app/api/v1/shared/streaming.py` (`PublicSseEvent`)
- **SSE endpoints (data-only):**
  - `apps/api-service/src/app/api/v1/chat/router.py` (`POST /api/v1/chat/stream`)
  - `apps/api-service/src/app/api/v1/workflows/router.py` (`POST /api/v1/workflows/{workflow_key}/run-stream`)
- **Contract playback tests (fixtures):** `apps/api-service/tests/contract/streams/test_stream_goldens.py`
  - Example fixtures live under `docs/contracts/public-sse-streaming/examples/`.

## Dependency map (what blocks what)

This is the sequencing we should follow to avoid “band-aid” fixes. When a gap is *blocked* by another, it means we cannot reliably validate or even observe the downstream behavior until the upstream gap is resolved.

| Gap | Blocked by | Why it’s blocked |
| --- | --- | --- |
| SE-GAP-003 (OpenAI `error` not UI-visible) | SE-GAP-001 | Workflow errors may never reach the browser if the workflow SSE stream isn’t parsed correctly. |
| SE-GAP-004 (terminal semantics missing) | SE-GAP-001 | Workflow terminal/error events can’t be validated if workflow events are dropped by the parser. |
| SE-GAP-005 (reasoning semantics + policy) | SE-GAP-002, SE-GAP-004 | Whether/what reasoning is safe to stream is a payload-policy decision; terminal semantics determines how “reasoning ended” is represented. |
| SE-GAP-006 (refusal semantics) | SE-GAP-002, SE-GAP-004 | Refusal is a user-visible terminal-ish condition; payload policy determines what refusal details may be exposed. |
| SE-GAP-007 (function tool args streaming) | SE-GAP-002 | Arguments may contain sensitive values; we need a policy before promoting them into a typed UI surface. |
| SE-GAP-008 (MCP streaming parity) | SE-GAP-002 | MCP tool args/results may be sensitive; we need a policy before streaming typed payloads. |
| SE-GAP-009 (hosted tool fidelity polish) | SE-GAP-002 (optional) | Status/code details can be safely promoted, but deciding how much raw payload is allowed affects the final shape. |

## Recommended redesign order (chronological)

The right way to do this “from the ground up” is to start with transport + contract invariants, then refine each event family.

1. **Transport correctness (SSE)**
   - Resolve SE-GAP-001 first: choose the canonical SSE framing and implement a single robust parser.
   - Goal: workflows and chat streams are equally parseable and observable end-to-end.

2. **Public vs internal boundary**
   - Resolve SE-GAP-002 next: decide what the browser is allowed to receive.
   - Goal: the “public stream contract” is safe-by-default; raw fidelity is either removed or explicitly sanitized.

3. **Stream semantics (terminal + error)**
   - Resolve SE-GAP-003 and SE-GAP-004 together: define a unified terminal/error model and enforce it in code + tests.
   - Goal: every stream ends deterministically and errors are always UI-visible.

4. **User-visible semantics**
   - Resolve SE-GAP-005 (reasoning) and SE-GAP-006 (refusal) using the policy decisions above.
   - Goal: we can explain exactly what we stream for reasoning/refusal and why, aligned with professional policy posture.

5. **Tool parity + polish**
   - Resolve SE-GAP-009 (hosted tools fidelity), then decide scope for SE-GAP-007 (function tools) and SE-GAP-008 (MCP).
   - Goal: typed tool surfaces are consistent across hosted tools / MCP / function tools (or intentionally scoped).

6. **Future-proofing + optional features**
   - Resolve SE-GAP-010 last: decide whether to keep forwarding unused raw event families to browsers, or keep them server-side until needed.

## Gap details + professional fix directions (options)

### SE-GAP-001 (P0) — SSE framing + parsing mismatch (workflows)

**What we saw**
- Chat SSE uses `data: <json>\n\n`.
- Workflow SSE uses full SSE fields: `id:`, `event:`, then `data:`.
- Frontend workflow parser currently only processes segments that **start** with `data: `, so it will skip workflow events.

**Professional fix options**
1. **Standardize backend framing**: emit `data:`-only across *all* endpoints (simple) and keep `event.kind` inside JSON.
2. **Standardize frontend parsing**: implement a real SSE parser (handles `id/event/data`) and accept both styles; prefer this if we want richer SSE semantics (`event:`) long-term.
3. **Both**: converge backend framing + add robust parser (best UX + least surprise; more work).

**Recommendation**
- Option 2 (or 3) is most professional: one parser, one spec, fewer edge cases; then align backend framing for consistency.

---

### SE-GAP-002 (P0) — Streaming payload redaction/truncation policy is missing

**What we saw**
- `response.created` payload can include `instructions` and tool configuration.
- Tool payloads can include large/sensitive fields (file excerpts, base64 images, logprobs).
- We currently stream `payload/raw_event` widely, with no explicit “public vs internal” contract boundary.

**Professional fix options**
1. **Sanitize-and-forward**: keep `payload/raw_event` but apply a strict allowlist/truncation policy per `raw_type` and per tool type.
2. **Derived-only contract**: stop forwarding `payload/raw_event` to browsers entirely; keep raw fidelity only in server logs/traces.
3. **Tiered contract**: “public” SSE for browsers + “debug” SSE for internal tooling (likely overkill for a starter repo).

**Recommendation**
- Option 2 or 1 (depending on how much debugging we want in the browser). For a production-grade starter, “derived-only + server traces” is cleanest.

---

### SE-GAP-003 (P0) — Error contract is inconsistent; OpenAI `type="error"` is not UI-visible

**What we saw**
- OpenAI error events are represented as `kind="raw_response_event", raw_type="error"`.
- Our UI listens for `kind="error"` and treats stream chunks of type `'error'` as fatal.
- OpenAI `type="error"` is not guaranteed to produce a terminal UI error event; also `is_terminal` is hardcoded false for raw events.

**Professional fix options**
1. **Translate provider errors**: map `raw_type="error"` and `response.failed` into `kind="error"` with a structured payload and `is_terminal=true`.
2. **Teach frontend to treat `raw_type="error"` as fatal** (less clean; spreads provider semantics into UI).

**Recommendation**
- Option 1: keep provider-neutral UI contract; treat all fatal conditions as `kind="error"` and terminal.

---

### SE-GAP-004 (P1) — Terminal semantics for failure/incomplete/queued are not explicit/tested

**What we saw**
- Some lifecycle failure states are “best-effort” and not covered by fixtures.
- We synthesize a terminal run-item event after stream completion; this can mask failures if the stream ends unexpectedly.

**Professional fix direction**
- Define and enforce invariants:
  - Every stream ends with exactly one terminal event.
  - Terminal event kind is either `error` or `final` (and `final` indicates success vs incomplete).
  - `response.failed`, `response.incomplete`, `raw_type="error"` must terminate with an `error` terminal event.
- Add deterministic tests around these invariants.

---

### SE-GAP-005 (P1) — Reasoning channel semantics + policy posture

**What we saw**
- We stream `reasoning_delta` for both `reasoning_text.delta` and `reasoning_summary_text.delta` but do not label which.
- UI displays “Reasoning” content, but we have no stream fixtures validating real model behavior.
- Potential policy/UX risk if `reasoning_text.*` represents full internal reasoning.

**Professional fix options**
1. **Summary-only**: stream only `reasoning_summary_*` to browsers; treat `reasoning_text.*` as server-only.
2. **Dual-channel**: stream both with a discriminator field and strict policy gating/redaction.

**Recommendation**
- Option 1: summary-only is the cleanest and most aligned with a security-first posture; rename UI label to “Reasoning summary” if needed.

---

### SE-GAP-006 (P1) — Refusal events are not first-class in the UI

**What we saw**
- `response.refusal.*` is passthrough-only; UI doesn’t render it as refusal (or error) today.

**Professional fix options**
1. Promote refusal into a typed surface (`refusal_delta/refusal_text`) and render it in the assistant message UI.
2. Translate refusal into `kind="error"` with a safe user-facing message + optional structured “refusal details”.

**Recommendation**
- Promote as a first-class UX concept (option 1) so product behavior is explicit and testable; keep messaging safe and policy-aligned.

---

### SE-GAP-007 (P2) — Function tool streaming visibility and coverage

**What we saw**
- Function-call argument events are passthrough-only and not fixture-covered.
- We use `@function_tool` tools (`get_current_time`, `search_conversations`) but haven’t validated what events are emitted.

**Professional fix direction**
- First record reality (manual test/fixture) and decide whether UI needs streaming arguments.
- If yes: normalize into `tool_call` (custom tool type) with redaction/truncation.
- If no: keep passthrough server-side only; rely on run-item events for tool timeline.

---

### SE-GAP-008 (P2) — MCP streaming parity (optional but desirable)

**What we saw**
- MCP tool registration is robust and tested, but streaming events are raw-only with no typed surface.

**Professional fix direction**
- Treat MCP like hosted tools:
  - typed `tool_call` representation (`tool_type="mcp"` with status/name/args),
  - optional manual test that uses a real MCP server when configured.

---

### SE-GAP-009 (P2) — Hosted tool fidelity gaps (polish)

**What we saw**
- `response.code_interpreter_call_code.done` is not promoted into `tool_call`.
- Some statuses are normalized in lossy ways (`web_search.searching` collapsed; `file_search.in_progress` mapped to searching).

**Professional fix direction**
- Close these gaps for completeness:
  - promote `*_code.done`,
  - preserve raw statuses in typed model (or include a `raw_status` field).

---

### SE-GAP-010 (P3) — “Done” fallbacks and unused raw events

**What we saw**
- `output_text.done` is not used as a fallback.
- `content_part.*` is forwarded but unused.
- Non-citation annotations remain raw-only.

**Professional fix direction**
- Decide what we support as “first-class” now (likely: text deltas + citations + tools + errors + refusal + reasoning summaries).
- Everything else: either drop from browser streams (keep server-side) or add explicit typed support when needed.

## Proposed discussion order (so we can decide and then implement)

1. SE-GAP-001 (SSE framing + parser) — unblock workflow streaming reliability.
2. SE-GAP-002 (payload policy) — define what is safe to stream.
3. SE-GAP-003/004 (error + terminal semantics) — correctness + UX.
4. SE-GAP-005/006 (reasoning + refusal) — user-visible semantics + policy posture.
5. SE-GAP-007/008/009/010 — tool parity + polish.

## Decisions (pending)

Fill these in as we agree on each redesign choice:

- [x] SSE framing standard: **`data-only`** everywhere (robust parser).
- [x] Public streaming payload policy: **`derived-only`** (no raw_event/payload in browsers).
- [x] Unified terminal event: **`kind="final"` + `final.status`** (`completed|failed|incomplete|refused|cancelled`).
- [x] Reasoning stance: **stream summaries only** (`response.reasoning_summary_*`), never “full reasoning” to browsers.
- [x] Refusal stance: **first-class refusal** (not translated to `error`).
- [x] Custom tools + MCP: **typed tool-call parity**, including streaming args (with redaction/truncation indicators).
