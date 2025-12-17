# Evaluation — OpenAI Responses API Streaming Events: Output Content (`02-output-content.md`)

**Source doc:** `docs/integrations/openai-responses-api/streaming-events/02-output-content.md`  
**Manifest:** `docs/integrations/openai-responses-api/streaming-events/manifest.json`  
**Last updated:** 2025-12-15  
**Status:** Resolved (Backend). Frontend migration pending.

## Scope

This tracker evaluates the Responses API *output/content* streaming event types:

- `response.output_item.added`
- `response.output_item.done`
- `response.content_part.added`
- `response.content_part.done`
- `response.output_text.delta`
- `response.output_text.done`
- `response.output_text.annotation.added`
- `response.refusal.delta`
- `response.refusal.done`

For each event, we answer:

- **Consume?** Does backend receive it from the SDK and map it into our domain stream?
- **Forward?** Does it reach the browser as an SSE payload?
- **Transform?** Do we rename/normalize/aggregate/redact any fields?
- **Mapping?** Where is the mapping implemented?
- **Tests?** What proves this behavior?

## Current architecture (source → contract)

### Backend (provider → domain)

- OpenAI Agents SDK stream → provider adapter → `AgentStreamEvent` domain DTO
  - **Domain DTO:** `apps/api-service/src/app/domain/ai/models.py` (`AgentStreamEvent`)
  - **OpenAI adapter:** `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
    - `_map_raw_response_event()` preserves `raw_type` + `sequence_number` and derives convenience fields:
      - `text_delta` for `response.output_text.delta`
      - `annotations` (citations only) for `response.output_text.annotation.added`
      - `tool_call` for selected tool-related `response.output_item.*` cases

### Backend (domain → API contract → SSE)

- `AgentStreamEvent` → **Public SSE Contract** via:
  - **Schemas:** `apps/api-service/src/app/api/v1/shared/streaming.py` (`PublicSseEvent`)
  - **Projector:** `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
- SSE endpoints (data-only):
  - **Chat:** `apps/api-service/src/app/api/v1/chat/router.py` (`POST /api/v1/chat/stream`)
  - **Workflows:** `apps/api-service/src/app/api/v1/workflows/router.py` (`POST /api/v1/workflows/{workflow_key}/run-stream`)

### Frontend (SSE → UI)

- **Status:** not migrated yet (out of scope for this backend milestone).
- Target contract is documented in `docs/contracts/public-sse-streaming/v1.md`.

## Coverage matrix — output/content events

Legend:
- **Consume?** = event arrives from OpenAI and is represented in our domain stream (`AgentStreamEvent`).
- **Forward?** = event reaches the browser as `PublicSseEvent` over SSE.
- **Transform?** = any semantic changes (not just wrapping).

| OpenAI event type | Consume? (backend) | Forward? (SSE) | Transform? | Mapping (source → contract) | Tests | Notes / gaps |
| --- | --- | --- | --- | --- | --- | --- |
| `response.output_item.added` | Yes | Yes (derived) | Derived-only | Drives tool metadata capture; browser sees `tool.status` / `tool.arguments.*` / `chunk.*` where applicable | Contract playback goldens | Raw items are not forwarded. |
| `response.output_item.done` | Yes | Yes (derived) | Derived-only | Drives tool completion projections (file search results, image generation metadata, etc.) | Contract playback goldens | Raw items are not forwarded. |
| `response.content_part.added` | Yes | No | Dropped | Not emitted in `public_sse_v1` | N/A | Out of scope for current UX. |
| `response.content_part.done` | Yes | No | Dropped | Not emitted in `public_sse_v1` | N/A | Out of scope for current UX. |
| `response.output_text.delta` | Yes | Yes | Derived-only | `kind="message.delta"` | Contract playback goldens | Primary assistant typing signal for UI. |
| `response.output_text.done` | Yes | No (today) | Dropped | Not emitted in `public_sse_v1` | N/A | `final.response_text` is authoritative. |
| `response.output_text.annotation.added` | Yes | Yes | Derived-only | `kind="message.citation"` (citation union only) | Contract playback goldens | Non-citation annotation types are intentionally not exposed. |
| `response.refusal.delta` | Yes (best-effort) | Yes | Derived-only | `kind="refusal.delta"` | Contract playback goldens | |
| `response.refusal.done` | Yes (best-effort) | Yes | Derived-only | `kind="refusal.done"` (+ terminal `final.status="refused"`) | Contract playback goldens | |

### Evidence pointers (where to look)

- **Raw Responses event capture:** `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
- **Projection (output/content kinds):** `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
- **Public schemas:** `apps/api-service/src/app/api/v1/shared/streaming.py`
- **Contract playback tests + fixtures:** `apps/api-service/tests/contract/streams/test_stream_goldens.py`, `docs/contracts/public-sse-streaming/examples/`

## Notes

- `public_sse_v1` is **derived-only**: no raw payloads are forwarded for output/content events.
- Refusals are first-class (`refusal.delta` / `refusal.done`) and terminate with `final.status="refused"`.
- Citations are supported via `message.citation` (citation union only).
