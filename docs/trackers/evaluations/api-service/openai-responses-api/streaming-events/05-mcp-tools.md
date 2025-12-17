# Evaluation — OpenAI Responses API Streaming Events: MCP Tools (`05-mcp-tools.md`)

**Source doc:** `docs/integrations/openai-responses-api/streaming-events/05-mcp-tools.md`  
**Manifest:** `docs/integrations/openai-responses-api/streaming-events/manifest.json`  
**Last updated:** 2025-12-15  
**Status:** Resolved (Backend). Frontend migration pending.

## Scope

This tracker evaluates Responses API streaming event types for hosted MCP tools:

- `response.mcp_call_arguments.delta`
- `response.mcp_call_arguments.done`
- `response.mcp_call.in_progress`
- `response.mcp_call.completed`
- `response.mcp_call.failed`
- `response.mcp_list_tools.in_progress`
- `response.mcp_list_tools.completed`
- `response.mcp_list_tools.failed`

For each event, we answer:
- **Consume?** Does backend receive/map it?
- **Forward?** Does it reach the browser?
- **Transform?** Do we normalize/aggregate/promote fields?
- **Mapping?** Where is the mapping implemented?
- **Tests?** What proves it?

## Current architecture (source → contract)

### Backend: “MCP-ready” tool registry (no default MCP tools shipped)

We intentionally do **not** ship a concrete MCP tool enabled by default, but we *do* provide the wiring so repo cloners can add them safely:

- **Settings model + validation:** `apps/api-service/src/app/core/settings/mcp.py`
  - Supports `MCP_TOOLS` JSON env var.
  - Enforces: unique names/labels, exactly one of `server_url` or `connector_id`, connector auth required, safe default `require_approval="always"`.
- **Tool registration:** `apps/api-service/src/app/utils/tools/registry.py`
  - Registers each configured entry as an `agents.HostedMCPTool` (wrapped as `NamedHostedMCPTool` so multiple instances coexist).
  - Approval handler defaults to “deny unless explicitly allow-listed” (`auto_approve_tools` / `deny_tools`).
- **Docs for operators:** `apps/api-service/src/app/agents/README.md` (“Adding hosted MCP tools”).

### Backend: streaming mapping (raw passthrough today)

- **Raw capture (provider):** `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
- **Public projection (derived-only):** `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
- **Public schemas:** `apps/api-service/src/app/api/v1/shared/streaming.py` (`McpTool`, `tool.arguments.*`, `tool.output`)

### Frontend visibility

- **Status:** not migrated yet (out of scope for this backend milestone).
- Target contract is documented in `docs/contracts/public-sse-streaming/v1.md`.
- **Persisted run items:** we already classify `mcp_call` as tool-related for conversation history:
  - `apps/api-service/src/app/services/agents/event_log.py` maps SDK session items with `type == "mcp_call"` into `ConversationEvent.run_item_type="mcp_call"`.
  - Frontend tool timeline treats `mcp_call` as tool-related (`apps/web-app/lib/chat/mappers/toolTimelineMappers.ts`).

## Coverage matrix — MCP tool streaming events

Legend:
- **Consume?** = event arrives from OpenAI and is represented in our stream.
- **Forward?** = event reaches the browser as `Streaming*Event` over SSE.
- **Transform?** = semantic changes (aggregation, typed promotion, redaction).

| OpenAI event type | Consume? (backend) | Forward? (SSE) | Transform? | Mapping (source → contract) | Tests | Notes / gaps |
| --- | --- | --- | --- | --- | --- | --- |
| `response.mcp_call_arguments.delta` | Best-effort | Yes (derived) | Derived-only + sanitized | `kind="tool.arguments.delta"` + `kind="tool.arguments.done"` | Contract playback goldens | Deltas are emitted as sanitized chunks; `tool.arguments.done` is authoritative. |
| `response.mcp_call_arguments.done` | Best-effort | Yes | Derived-only + sanitized | `kind="tool.arguments.done"` (`arguments_text` + best-effort `arguments_json`) | Contract playback goldens | |
| `response.mcp_call.in_progress` | Best-effort | Yes | Derived-only | `kind="tool.status"` with `tool_type="mcp"` + `status="in_progress"` | Contract playback goldens | Approval requests surface as `status="awaiting_approval"` via run-item events. |
| `response.mcp_call.completed` | Best-effort | Yes | Derived-only | `kind="tool.status"` with `status="completed"` | Contract playback goldens | |
| `response.mcp_call.failed` | Best-effort | Yes | Derived-only | `kind="tool.status"` with `status="failed"` | (No fixture yet) | Provider hard errors may also terminate with `kind="error"`. |
| `response.mcp_list_tools.*` | Best-effort | No | Dropped | Not emitted in `public_sse_v1` | N/A | Out of scope for current UX. |

## Evidence pointers (where to look)

- Settings + validation: `apps/api-service/src/app/core/settings/mcp.py:1`
- MCP tool registration + approval: `apps/api-service/src/app/utils/tools/registry.py:200`
- Tool registry MCP tests: `apps/api-service/tests/unit/agents/tools/test_tools.py:1`
- Settings validation tests: `apps/api-service/tests/unit/config/test_settings_mcp.py:1`
- Raw Responses capture: `apps/api-service/src/app/infrastructure/providers/openai/streaming.py`
- Public projection: `apps/api-service/src/app/api/v1/shared/public_stream_projector.py`
- Contract fixtures: `docs/contracts/public-sse-streaming/examples/chat-mcp-tool.ndjson`
- Contract playback tests: `apps/api-service/tests/contract/streams/test_stream_goldens.py`
- Conversation event log classification (`mcp_call`): `apps/api-service/src/app/services/agents/event_log.py:1`
- Frontend tool timeline recognizes `mcp_call`: `apps/web-app/lib/chat/mappers/toolTimelineMappers.ts:1`

## Notes

- The repo remains MCP-capable by configuration (safe defaults and strict settings validation).
- `public_sse_v1` includes a typed MCP streaming surface (`tool.status`, `tool.arguments.*`, `tool.output`).
