# Evaluation — OpenAI Responses API Streaming Events: Lifecycle (`01-lifecycle.md`)

**Source doc:** `docs/integrations/openai-responses-api/streaming-events/01-lifecycle.md`  
**Manifest:** `docs/integrations/openai-responses-api/streaming-events/manifest.json`  
**Last updated:** 2025-12-15  
**Status:** Resolved (Backend). Frontend migration pending.

## Scope

This tracker evaluates the Responses API *lifecycle* streaming event types:

- `response.created`
- `response.in_progress`
- `response.completed`
- `response.failed`
- `response.incomplete`
- `response.queued`

For each event, we answer:

- **Consume?** Does backend receive it from the SDK and map it into our domain stream?
- **Forward?** Does it reach the browser as an SSE payload?
- **Transform?** Do we rename/normalize/aggregate/redact any fields?
- **Mapping?** Where is the mapping implemented?
- **Tests?** What proves this behavior?

## Current architecture (source → contract)

### Backend (provider → domain)

- The OpenAI Agents SDK produces stream events like `raw_response_event`.
- We map SDK stream events into a provider-neutral domain envelope:
  - **Domain DTO:** `apps/api-service/src/app/domain/ai/models.py` (`AgentStreamEvent`)
  - **OpenAI adapter:** `apps/api-service/src/app/infrastructure/providers/openai/streaming.py` (`OpenAIStreamingHandle`)
    - `_map_raw_response_event()` pulls `data.type` into `raw_type` and forwards the raw JSON-ish payload.

### Backend (domain → API contract → SSE)

- We project domain events into the **derived-only public SSE contract**:
  - **Schemas:** `apps/api-service/src/app/api/v1/shared/streaming.py` (`PublicSseEvent`)
  - **Projector:** `apps/api-service/src/app/api/v1/shared/public_stream_projector.py` (`PublicStreamProjector`)
- We stream them via **data-only SSE**:
  - **Chat stream:** `apps/api-service/src/app/api/v1/chat/router.py` (`POST /api/v1/chat/stream`)
  - **Workflow stream:** `apps/api-service/src/app/api/v1/workflows/router.py` (`POST /api/v1/workflows/{workflow_key}/run-stream`)

### Frontend (SSE → typed events)

- **Status:** not migrated yet (out of scope for this backend milestone).
- Target contract is documented in `docs/contracts/public-sse-streaming/v1.md`.

## Coverage matrix — lifecycle events

Legend:
- **Consume?** = event arrives from OpenAI and is represented in our domain stream (`AgentStreamEvent`).
- **Forward?** = event reaches the browser as `Streaming*Event` over SSE.
- **Transform?** = any semantic changes (not just wrapping).

| OpenAI event type | Consume? (backend) | Forward? (SSE) | Transform? | Mapping (source → contract) | Tests | Notes / gaps |
| --- | --- | --- | --- | --- | --- | --- |
| `response.created` | Yes | Yes | Derived-only | `kind="lifecycle"` + `status="in_progress"` | Contract playback goldens | `response_id` may be `null` early. |
| `response.in_progress` | Yes | Yes | Derived-only | `kind="lifecycle"` + `status="in_progress"` | Contract playback goldens | Used for progress UI. |
| `response.completed` | Yes | Yes | Derived-only | `kind="lifecycle"` + `status="completed"` | Contract playback goldens | Terminal is emitted separately as `kind="final"` (exactly once). |
| `response.failed` | Yes (best-effort) | Yes (best-effort) | Derived-only | `kind="lifecycle"` + `status="failed"` (+ terminal `final.status="failed"` when available) | Contract playback goldens | Provider hard errors map to terminal `kind="error"`. |
| `response.incomplete` | Yes (best-effort) | Yes (best-effort) | Derived-only | `kind="lifecycle"` + `status="incomplete"` (+ terminal `final.status="incomplete"`) | Contract playback goldens | |
| `response.queued` | Yes (best-effort) | Yes (best-effort) | Derived-only | `kind="lifecycle"` + `status="queued"` | (No fixture yet) | Rare unless we opt into queued/background behavior. |

### Evidence pointers (where to look)

- **Backend raw event capture:** `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
- **Public projection:** `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
- **Public schemas:** `apps/api-service/src/app/api/v1/shared/streaming.py`
- **SSE endpoints:** `apps/api-service/src/app/api/v1/chat/router.py`, `apps/api-service/src/app/api/v1/workflows/router.py`
- **Contract playback tests:** `apps/api-service/tests/contract/streams/test_stream_goldens.py`
- **Workflow example fixture:** `docs/contracts/public-sse-streaming/examples/workflow-analysis-code.ndjson`

## Notes

- The public contract is **derived-only**: browser clients do not receive raw `response` payloads.
- Terminal semantics are explicit and tested: streams end with exactly one terminal event (`final` or `error`).
- Chat and workflow streams use the same SSE framing: `data: <json>\n\n` (with optional heartbeat comments).
