# Evaluation — OpenAI Responses API Streaming Events: Reasoning (`06-reasoning.md`)

**Source doc:** `docs/integrations/openai-responses-api/streaming-events/06-reasoning.md`  
**Manifest:** `docs/integrations/openai-responses-api/streaming-events/manifest.json`  
**Last updated:** 2025-12-15  
**Status:** Resolved (Backend). Frontend migration pending.

## Scope

This tracker evaluates Responses API streaming event types related to reasoning output:

- `response.reasoning_summary_part.added`
- `response.reasoning_summary_part.done`
- `response.reasoning_summary_text.delta`
- `response.reasoning_summary_text.done`
- `response.reasoning_text.delta`
- `response.reasoning_text.done`

For each event, we answer:

- **Consume?** Does backend receive it from the SDK and map it into our domain stream?
- **Forward?** Does it reach the browser as an SSE payload?
- **Transform?** Do we rename/normalize/aggregate/redact any fields?
- **Mapping?** Where is the mapping implemented?
- **Tests?** What proves this behavior?

## Current architecture (source → contract)

### Backend (provider → domain)

- The OpenAI Agents SDK emits `raw_response_event` items where `data.type` is the Responses API event type string.
- We map raw events into `AgentStreamEvent` and derive a small set of convenience fields:
  - **OpenAI adapter:** `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
  - **Domain DTO:** `apps/api-service/src/app/domain/ai/models.py`
  - **Reasoning delta derivation:** `apps/api-service/src/app/infrastructure/providers/openai/streaming.py:105`
    - Sets `AgentStreamEvent.reasoning_delta` for:
      - `response.reasoning_text.delta`
      - `response.reasoning_summary_text.delta`

### Backend (domain → API contract → SSE)

- `AgentStreamEvent` → **Public SSE Contract** via:
  - `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
  - `apps/api-service/src/app/api/v1/shared/streaming.py` (includes `reasoning_summary.delta`)
- SSE endpoints:
  - `apps/api-service/src/app/api/v1/chat/router.py` (`POST /api/v1/chat/stream`)
  - `apps/api-service/src/app/api/v1/workflows/router.py` (`POST /api/v1/workflows/{workflow_key}/run-stream`)

### Frontend (SSE → UI)

- **Status:** not migrated yet (out of scope for this backend milestone).
- Target contract is documented in `docs/contracts/public-sse-streaming/v1.md` (summary-only).

## Coverage matrix — reasoning events

Legend:
- **Consume?** = event arrives from OpenAI and is represented in our domain stream (`AgentStreamEvent`).
- **Forward?** = event reaches the browser as `Streaming*Event` over SSE.
- **Transform?** = semantic changes (derived fields, redaction, aggregation).

| OpenAI event type | Consume? (backend) | Forward? (SSE) | Transform? | Mapping (source → contract) | Tests | Notes / gaps |
| --- | --- | --- | --- | --- | --- | --- |
| `response.reasoning_summary_part.added` | Yes (best-effort) | No | Dropped | Not emitted in `public_sse_v1` | N/A | |
| `response.reasoning_summary_part.done` | Yes (best-effort) | No | Dropped | Not emitted in `public_sse_v1` | N/A | |
| `response.reasoning_summary_text.delta` | Yes | Yes | Derived-only | `kind="reasoning_summary.delta"` | Contract playback goldens | Summary-only is browser-safe. |
| `response.reasoning_summary_text.done` | Yes (best-effort) | Yes (fallback) | Derived-only | `kind="reasoning_summary.delta"` (done fallback emits missing text) | Contract playback goldens | |
| `response.reasoning_text.delta` | Yes | No | Dropped | Not emitted in `public_sse_v1` | N/A | Treated as server-only. |
| `response.reasoning_text.done` | Yes (best-effort) | No | Dropped | Not emitted in `public_sse_v1` | N/A | Treated as server-only. |

### Evidence pointers (where to look)

- Raw Responses capture: `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
- Projection (reasoning summary): `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
- Contract fixture: `docs/contracts/public-sse-streaming/examples/chat-reasoning-summary.ndjson`
- Contract playback tests: `apps/api-service/tests/contract/streams/test_stream_goldens.py`

## Notes

- Public streams are **summary-only**: only `response.reasoning_summary_*` is projected to the browser.
- A deterministic fixture (`chat-reasoning-summary.ndjson`) validates end-to-end contract playback.
