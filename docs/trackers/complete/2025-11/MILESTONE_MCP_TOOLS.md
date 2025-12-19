# Milestone: MCP Tool Enablement (Backend)

Status: Completed
Owner: Platform Foundations
Goal: Allow developers to register hosted MCP tools (remote MCP servers or OpenAI connectors) via settings → tool registry → agent tool_keys with no spec changes.

## Phases

### Phase 1 — Planning & tracker
- [x] Create milestone tracker with scope and safety posture

### Phase 2 — Config + registry wiring
- [x] Add MCP settings mixin with validation (name uniqueness; server_url xor connector_id; connector auth check; default require_approval="always")
- [x] Wire HostedMCPTool registration in the tool registry with metadata + categories
- [x] Preserve existing hosted tools (search, code, image) behavior
- [x] Run `hatch run lint` + `hatch run typecheck` after implementation

### Phase 3 — Docs + tests + verification
- [x] Add developer doc snippet to `app/agents/README.md` describing how to add MCP tools via settings + tool_keys
- [x] Unit tests for settings parsing/validation and registry registration of an MCP tool
- [x] Run `hatch run lint` + `hatch run typecheck`

## Definition of Done
- Settings support multiple hosted MCP tool definitions with safe defaults
- Tool registry registers MCP tools when configured; agents can include them via `tool_keys`
- Documentation updated; unit coverage for settings + registry; lint/typecheck green
