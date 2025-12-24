# Milestone: Full-Fidelity Conversation History & Replay

Status: In progress (updated 2025-11-29)  
Owner: Platform Foundations  
Created: 2025-11-29  
Goal: Persist and surface complete agent context (messages, tool calls, MCP calls, reasoning traces, approvals, attachments) with clean replay for both SDK and product surfaces.

## Outcomes
- SDK session store stays canonical for provider replay; Postgres event log becomes the product-facing source for history/search/UX.
- New event log stores structured run items (message/tool/reasoning) with ordering, tool metadata, arguments, outputs, and deltas.
- History UI/API can render prior tool calls and reasoning without rebuilding from SDK blobs.
- Observability, retention, and recovery paths documented and tested.

## Phases
### Phase 0 — Design sign-off
- Align on data model (event log schema, ordering, indexes, retention split).  
- Confirm source-of-truth boundaries: SDK session tables vs projection tables.  
- Confirm rollout guardrails (no backfill required for greenfield).  
Status: ✅

### Phase 1 — Schema & migrations
- Add `agent_run_events` table (one row per run item) with indexes on `(conversation_id, sequence_no)` and `(tool_call_id)`; JSONB for arguments/outputs.  
- Keep existing `agent_messages` for text/search; decide whether to denormalize summary rows.  
- Update Alembic migration; integration test coverage for migrations.  
Status: ✅ (agent_run_events table + indexes merged and migrated)

### Phase 2 — Ingestion pipeline
- Hook run completion/stream drain to project SDK run items into `agent_run_events` in order.  
- Capture tool_called/tool_output/MCP/approval/reasoning_text.delta; store model + agent name.  
- Ensure idempotence per response_id/sequence_no.  
Status: ✅ (run events projected with sequence ordering + idempotent keys)

### Phase 3 — Read APIs & UI contract
- Extend conversation read endpoint to return ordered event log (filterable to displayable items).  
- Add lightweight transcript mode (messages only) and full-fidelity mode (includes tool/reasoning).  
- Update frontend query/hook + renderers to show tool calls, arguments, outputs, reasoning text.  
Status: ✅ (transcript/full modes exposed via /conversations/{id}/events; frontend rendering still to polish)

### Phase 4 — Observability & retention
- Metrics: ingestion latency, event-count per run, replay latency.  
- Alerts on event projection failures and drift between SDK session count and event log count.  
- Retention policy: shorter TTL for `sdk_agent_session_messages`, longer for `agent_run_events`; document cleanup job.  
Status: ✅ (metrics + drift gauge emitted; cleanup job + TTL config; sample Prometheus alert rules + Grafana layout; runbook/retention docs for adopters; compatible with bundled optional OpenTelemetry collector or external Prometheus/Grafana)

## Scope & non-goals
- In scope: structured history storage, projection, API/UI rendering, observability, retention.  
- Not in scope: vector/semantic search, cross-tenant analytics, per-user export tooling.

## Risks / mitigations
- **Data volume**: tool call payloads could bloat storage → cap payload size, compress JSONB if needed, TTL on session tables.  
- **Drift**: projection might miss events → idempotent writes keyed by response_id + sequence_no; drift alerting.  
- **PII leakage**: tool args may contain sensitive data → configurable redaction paths + audit logging.

## Definition of Done
- New schema migrated in all envs; CI green.  
- Event log populated for new runs.  
- UI shows past tool calls & reasoning for existing conversations.  
- Runbook documents recovery/rebuild + retention settings.  
- Tracker archived with sign-off.
