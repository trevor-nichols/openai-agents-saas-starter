# Evaluation — OpenAI Responses API Streaming Events: Errors (`07-errors.md`)

**Source doc:** `docs/integrations/openai-responses-api/streaming-events/07-errors.md`  
**Manifest:** `docs/integrations/openai-responses-api/streaming-events/manifest.json`  
**Last updated:** 2025-12-15  
**Status:** Resolved (Backend). Frontend migration pending.

## Scope

This tracker evaluates the Responses API streaming event type:

- `error`

For this event, we answer:

- **Consume?** Does backend receive it from the SDK and map it into our domain stream?
- **Forward?** Does it reach the browser as an SSE payload?
- **Transform?** Do we rename/normalize/aggregate/redact any fields?
- **Mapping?** Where is the mapping implemented?
- **Tests?** What proves this behavior?

## Current architecture (source → contract)

### Backend (provider → domain)

- The OpenAI Agents SDK emits `raw_response_event` items whose `data.type` is the Responses API event type string.
- We map raw events into `AgentStreamEvent`:
  - **OpenAI adapter:** `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
  - **Domain DTO:** `apps/api-service/src/app/domain/ai/models.py`

For `type="error"`, the OpenAI adapter still represents it as:
- `AgentStreamEvent.kind="raw_response_event"`
- `AgentStreamEvent.raw_type="error"`
- `AgentStreamEvent.payload/raw_event` retains `{ code, message, param, sequence_number, type }` for server-side diagnostics

### Backend (domain → API contract → SSE)

- `AgentStreamEvent` → **Public SSE Contract** via:
  - `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
  - `apps/api-service/src/app/api/v1/shared/streaming.py` (`ErrorEvent`, `FinalEvent`)
- SSE endpoints:
  - **Chat:** `apps/api-service/src/app/api/v1/chat/router.py` (`POST /api/v1/chat/stream`)
  - **Workflows:** `apps/api-service/src/app/api/v1/workflows/router.py` (`POST /api/v1/workflows/{workflow_key}/run-stream`)

### Public error contract (terminal)

All UI-visible errors are normalized into a terminal `kind="error"` event:

- Provider errors (`raw_type="error"`) → `ErrorEvent.error.source="provider"`
- Server exceptions → `ErrorEvent.error.source="server"`

## Coverage matrix — error event

Legend:
- **Consume?** = event arrives from OpenAI and is represented in our domain stream (`AgentStreamEvent`).
- **Forward?** = event reaches the browser as `Streaming*Event` over SSE.
- **Transform?** = semantic changes (promotion to first-class error, terminal semantics, redaction).

| OpenAI event type | Consume? (backend) | Forward? (SSE) | Transform? | Mapping (source → contract) | Tests | Notes / gaps |
| --- | --- | --- | --- | --- | --- | --- |
| `error` | Yes (best-effort) | Yes | Yes (promote + terminal) | `kind="error"` (`source="provider"`) | Contract playback goldens | Exactly one terminal event is enforced in contract tests. |

### Evidence pointers (where to look)

- Raw Responses capture: `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
- Public projection: `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
- SSE endpoints: `apps/api-service/src/app/api/v1/chat/router.py`, `apps/api-service/src/app/api/v1/workflows/router.py`
- Contract fixture: `docs/contracts/public-sse-streaming/examples/chat-provider-error.ndjson`
- Contract playback tests: `apps/api-service/tests/contract/streams/test_stream_goldens.py`

## Notes

- Provider and server errors share a single UI-facing terminal event (`kind="error"`).
- Workflow and chat streams use the same framing, so errors are visible consistently to SSE parsers.
