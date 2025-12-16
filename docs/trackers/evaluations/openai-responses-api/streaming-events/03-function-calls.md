# Evaluation — OpenAI Responses API Streaming Events: Function Calls (`03-function-calls.md`)

**Source doc:** `docs/integrations/openai-responses-api/streaming-events/03-function-calls.md`  
**Manifest:** `docs/integrations/openai-responses-api/streaming-events/manifest.json`  
**Last updated:** 2025-12-15  
**Status:** Resolved (Backend). Frontend migration pending.

## Scope

This tracker evaluates the Responses API streaming event types related to custom tools / function calls:

- `response.function_call_arguments.delta`
- `response.function_call_arguments.done`
- `response.custom_tool_call_input.delta`
- `response.custom_tool_call_input.done`

For each event, we answer:

- **Consume?** Does backend receive it from the SDK and map it into our domain stream?
- **Forward?** Does it reach the browser as an SSE payload?
- **Transform?** Do we rename/normalize/aggregate/redact any fields?
- **Mapping?** Where is the mapping implemented?
- **Tests?** What proves this behavior?

## Current architecture (source → contract)

### Backend (provider → domain)

- The OpenAI Agents SDK emits `raw_response_event` items whose `data.type` matches the Responses API event type strings.
- We map every raw Responses event into our provider-neutral `AgentStreamEvent` envelope:
  - **OpenAI adapter:** `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
  - **Domain DTO:** `apps/api-service/src/app/domain/ai/models.py`

### Backend (domain → API contract → SSE)

- `AgentStreamEvent` → **Public SSE Contract** via:
  - `apps/api-service/src/app/api/v1/shared/streaming.py` (`PublicSseEvent`)
  - `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
- SSE endpoints:
  - `apps/api-service/src/app/api/v1/chat/router.py` (`POST /api/v1/chat/stream`)
  - `apps/api-service/src/app/api/v1/workflows/router.py` (`POST /api/v1/workflows/{workflow_key}/run-stream`)

### Where we actually use function tools today

We do have Agents SDK **function tools** (custom tools) registered and used by agents:

- Built-in function tools registered via `function_tool`:
  - `apps/api-service/src/app/infrastructure/providers/openai/registry/__init__.py` (`get_current_time`, `search_conversations`)
- Agents that request these tool keys:
  - `apps/api-service/src/app/agents/triage/spec.py`
  - `apps/api-service/src/app/agents/director/spec.py`

So these Responses event types are relevant for our codebase and are promoted into first-class `public_sse_v1` tool argument events.

## Coverage matrix — function-call streaming events

Legend:
- **Consume?** = event arrives from OpenAI and is represented in our domain stream (`AgentStreamEvent`).
- **Forward?** = event reaches the browser as `Streaming*Event` over SSE.
- **Transform?** = any semantic changes (not just wrapping).

| OpenAI event type | Consume? (backend) | Forward? (SSE) | Transform? | Mapping (source → contract) | Tests | Notes / gaps |
| --- | --- | --- | --- | --- | --- | --- |
| `response.function_call_arguments.delta` | Yes (best-effort) | Yes (derived) | Derived-only + sanitized | `kind="tool.arguments.delta"` + `kind="tool.arguments.done"` | Contract playback goldens | Deltas are emitted as sanitized chunks; `tool.arguments.done` is authoritative. |
| `response.function_call_arguments.done` | Yes (best-effort) | Yes | Derived-only + sanitized | `kind="tool.arguments.done"` (`arguments_text` + best-effort `arguments_json`) | Contract playback goldens | Sensitive keys redacted; strings truncated with `notices[]`. |
| `response.custom_tool_call_input.delta` | Yes (best-effort) | Yes (derived) | Derived-only + sanitized | `kind="tool.arguments.delta"` + `kind="tool.arguments.done"` | Contract playback goldens | Represented as `tool_type="function"` in the public contract. |
| `response.custom_tool_call_input.done` | Yes (best-effort) | Yes | Derived-only + sanitized | `kind="tool.arguments.done"` | Contract playback goldens | Input may be non-JSON; we still truncate and surface `arguments_text`. |

### Evidence pointers (where to look)

- **Raw Responses capture:** `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
- **Projection (function args):** `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
- **Function tool registration:** `apps/api-service/src/app/infrastructure/providers/openai/registry/__init__.py:241`
- **Agents requesting custom tool keys:** `apps/api-service/src/app/agents/triage/spec.py:1`, `apps/api-service/src/app/agents/director/spec.py:1`
- **Contract fixtures:** `docs/contracts/public-sse-streaming/examples/chat-function-tool.ndjson`
- **Contract playback tests:** `apps/api-service/tests/contract/streams/test_stream_goldens.py`
- **Manual recording (opt-in):** `apps/api-service/tests/manual/test_function_tool_manual.py`

## Notes

- Function tool arguments are a first-class UX surface in `public_sse_v1` (`tool.arguments.*`).
- The public stream is derived-only: no raw provider payloads are forwarded.
