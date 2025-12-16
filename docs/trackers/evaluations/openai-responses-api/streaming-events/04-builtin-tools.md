# Evaluation — OpenAI Responses API Streaming Events: OpenAI Hosted Tools (`04-builtin-tools.md`)

**Source doc:** `docs/integrations/openai-responses-api/streaming-events/04-builtin-tools.md`  
**Manifest:** `docs/integrations/openai-responses-api/streaming-events/manifest.json`  
**Last updated:** 2025-12-15  
**Status:** Resolved (Backend). Frontend migration pending.

## Scope

This tracker evaluates Responses API streaming event types for OpenAI hosted tools:

**File search**
- `response.file_search_call.in_progress`
- `response.file_search_call.searching`
- `response.file_search_call.completed`

**Web search**
- `response.web_search_call.in_progress`
- `response.web_search_call.searching`
- `response.web_search_call.completed`

**Image generation**
- `response.image_generation_call.in_progress`
- `response.image_generation_call.generating`
- `response.image_generation_call.partial_image`
- `response.image_generation_call.completed`

**Code interpreter**
- `response.code_interpreter_call.in_progress`
- `response.code_interpreter_call.interpreting`
- `response.code_interpreter_call.completed`
- `response.code_interpreter_call_code.delta`
- `response.code_interpreter_call_code.done`

For each event, we answer:
- **Consume?** Does backend receive/map it?
- **Forward?** Does it reach the browser?
- **Transform?** Do we normalize/aggregate/promote fields?
- **Mapping?** Where is the mapping implemented?
- **Tests?** What proves it?

## Current architecture (source → contract)

### Backend: tools in use

We use OpenAI hosted tools via the Agents SDK tool classes:

- Tool registration: `apps/api-service/src/app/utils/tools/registry.py`
  - `WebSearchTool`, `FileSearchTool`, `CodeInterpreterTool`, `ImageGenerationTool`
- Agents opt into tools via `tool_keys` (examples):
  - Web search: `apps/api-service/src/app/agents/researcher/spec.py`, `apps/api-service/src/app/agents/company_intel/spec.py`
  - File search: `apps/api-service/src/app/agents/retriever/spec.py` (and manual tests inject `context.vector_store_id`)
  - Code interpreter: `apps/api-service/src/app/agents/code_assistant/spec.py`, `apps/api-service/src/app/agents/pdf_designer/spec.py`
  - Image generation: `apps/api-service/src/app/agents/image_studio/spec.py`

### Backend: OpenAI stream → domain stream

The Agents SDK emits `raw_response_event` objects that wrap the underlying Responses API event union. We map them into a provider-neutral envelope:

- **OpenAI adapter:** `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
- **Domain DTO:** `apps/api-service/src/app/domain/ai/models.py` (`AgentStreamEvent`)

For hosted tools we additionally synthesize a typed `tool_call` payload (our contract) from either:

- raw Responses events (`raw_type` prefixed by `response.<tool>_call.*`), and/or
- `response.output_item.*` events that carry the full tool-call object.

### Backend: domain → public contract → SSE

- `AgentStreamEvent` → `PublicSseEvent` via `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
- Public tool schemas live in `apps/api-service/src/app/api/v1/shared/streaming.py` (`PublicTool` union).
- SSE endpoints (data-only):
  - `apps/api-service/src/app/api/v1/chat/router.py` (`POST /api/v1/chat/stream`)
  - `apps/api-service/src/app/api/v1/workflows/router.py` (`POST /api/v1/workflows/{workflow_key}/run-stream`)

### Frontend: what consumes these

- **Status:** not migrated yet (out of scope for this backend milestone).
- Target contract is documented in `docs/contracts/public-sse-streaming/v1.md`.

## Coverage matrix — hosted tool streaming events

Legend:
- **Consume?** = event arrives from OpenAI and is represented in our stream.
- **Forward?** = event reaches the browser as `PublicSseEvent` over SSE.
- **Transform?** = semantic changes (typed promotion, aggregation, storage side-effects).

| OpenAI event type | Consume? (backend) | Forward? (SSE) | Transform? | Mapping (source → contract) | Tests | Notes / gaps |
| --- | --- | --- | --- | --- | --- | --- |
| `response.file_search_call.*` | Yes | Yes | Derived-only | `kind="tool.status"` with `tool_type="file_search"` and status parity (`in_progress|searching|completed`) | Contract playback goldens | Results are attached to the `tool.status` payload when available (`response.output_item.done`). |
| `response.web_search_call.*` | Yes | Yes | Derived-only | `kind="tool.status"` with `tool_type="web_search"` and status parity (`in_progress|searching|completed`) | Contract playback goldens | `message.citation` events are emitted for citations; URLs are also attached as `sources` when available. |
| `response.image_generation_call.*` | Yes | Yes | Derived-only + chunking + storage | `kind="tool.status"` with `tool_type="image_generation"`; partial previews stream via `chunk.delta` for `partial_image_b64`; finals are stored and referenced via `final.attachments` | Contract playback goldens | Base64 previews are chunked; large binaries are not emitted inline. |
| `response.code_interpreter_call.*` | Yes | Yes | Derived-only | `kind="tool.status"` with `tool_type="code_interpreter"` and status parity (`in_progress|interpreting|completed`) | Contract playback goldens | |
| `response.code_interpreter_call_code.delta` | Yes | Yes | Derived-only | `kind="tool.code.delta"` | Contract playback goldens | |
| `response.code_interpreter_call_code.done` | Yes | Yes | Derived-only | `kind="tool.code.done"` | Contract playback goldens | Closed: now promoted as a first-class event. |

### Evidence pointers (where to look)

- Hosted tool registry: `apps/api-service/src/app/utils/tools/registry.py:1`
- Raw Responses capture: `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
- Public projection: `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
- Public tool schemas: `apps/api-service/src/app/api/v1/shared/streaming.py`
- Image persistence during streaming: `apps/api-service/src/app/services/agents/attachments.py:25`
- Contract playback tests + fixtures: `apps/api-service/tests/contract/streams/test_stream_goldens.py`, `docs/contracts/public-sse-streaming/examples/`
- Manual streaming tests (opt-in): `apps/api-service/tests/manual/README.md`

## Notes

- Hosted tool timelines are first-class in `public_sse_v1` via `tool.status`, `tool.code.*`, and (for images) `chunk.*` + `final.attachments`.
- Large image previews are chunked; final binaries are stored server-side and referenced from the terminal event.
