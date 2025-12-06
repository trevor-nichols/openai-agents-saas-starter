# Milestone: HeyAPI Regeneration Integration (Frontend)

Status: In Progress (starting with M1 — Chat Schema Alignment)  
Owner: Platform Foundations — Frontend  
Goal: Integrate the regenerated HeyAPI surface into the Next.js app, upgrade chat flows to the new schemas (attachments, structured output, run options), and stage future features (workflows, containers, vector stores, storage) with clear testing and observability.

## Scope
- Frontend only (web-app): generated SDK usage, server actions, queries, UI, and tests.
- No backend changes in this milestone; backend artifacts are treated as source of truth.
- Target environments: local + staging; pre-GA, no feature flags.

## Phases and Tasks

### M0 — Baseline & Guardrails (Planned)
- [x] Record regen delta summary and control branch.
- [x] Ensure `pnpm lint` / `pnpm type-check` pass on main (baseline).
- [x] Add brief changelog entry in `docs/trackers/SDK_CHANGES.md`.
- Sign-off: ✅

### M1 — Chat Schema Alignment (Complete)
- [x] Propagate `structured_output` and `attachments` through chat client/server layers (`lib/api/chat.ts`, `lib/server/services/chat.ts`, `lib/server/streaming/chat.ts`, `lib/queries/chat.ts`, `lib/chat/controller/useChatController.ts`).
- [x] Extend chat UI to render attachments + structured output (components under `components/ui/ai/*` and any feature wrappers).
- [x] Update domain types (`lib/chat/types.ts`) to include attachments and structured output; ensure SSE parsing tolerates new fields.
- [x] Tests: expand `lib/chat/__tests__` and `app/api/chat/*` route tests for new payloads; snapshot or fixture updates as needed.
- [x] Accessibility/UX: empty/loading/error states for attachments.
- Sign-off: ✅ Chat schema aligned; lint/type-check green

### M2 — Storage Attachment Enablement (Complete)
- [x] Add helper for presigned download (`getDownloadUrlApiV1StorageObjectsObjectIdDownloadUrlGet`) and wire into attachment rendering.
- [x] Handle missing/expired URLs gracefully; display filename/mime/size metadata.
- [x] Tests: `lib/api/__tests__/storage.test.ts` coverage for presign usage and error cases.
- Sign-off: ✅ Presign helper wired; UI fetch/refresh flow added; lint/type-check green

### M3 — Advanced Run Controls (Complete)
- [x] Expose `run_options` in chat server actions and UI controls (max_turns, previous_response_id, handoff_input_filter, run_config).
- [x] Validate payload input (run_config JSON parse) with user-facing error.
- [x] Tests for payload shaping and streaming request body coverage.
- Sign-off: ✅ Run controls plumbed client→server; lint/type-check green

### M4 — Workflows v1 (Complete)
- [x] Queries/services for `listWorkflows`, `runWorkflow`, `runWorkflowStream`, `getWorkflowRun` (mockable via `USE_API_MOCK`).
- [x] Feature scaffold `features/workflows/` with list + run UI; streaming placeholder wired.
- [x] Tests: lint/type-check green; streaming body parsing exercises covered via chat analogs (initial scaffold smoke-tested).
- Sign-off: ✅ Workflow feature scaffold landed; ready to swap mocks for live endpoints

### M5 — Storage & Vector Assets (Complete)
- [x] Storage objects: list, presign upload, download, delete.
- [x] Vector stores: list/create/get/delete; file attach/list/delete/get; semantic search.
- [x] Lightweight UI (admin-friendly) using existing data-access patterns.
- [x] Ensure tenant headers (`X-Tenant-Id`, `X-Tenant-Role`) set where required.
- Sign-off: ✅ Storage/vector scaffolds shipped with mock-friendly UI; lint/type-check green

### M6 — Containers & Agent Binding (Complete)
- [x] Queries for container CRUD and bind/unbind agent→container.
- [x] Surface container status in `app/(app)/agents` with attach/detach flows.
- [x] Tests/quality: lint/type-check green; mock-friendly data path via `USE_API_MOCK`.
- Sign-off: ✅ Containers data layer + agents UI tab; ready for live backend swap

### M7 — Observability & Regression (Complete)
- [x] Extend logging/telemetry for new fields in server actions and streaming handlers (chat stream logging for new payloads; attachment link resolution logs).
- [x] Storybook stories for chat attachments/structured outputs.
- [x] Run lint/type-check suites; add targeted interaction tests (story render & stream log test).
- Sign-off: ✅ Observability/story coverage in place; lint/type-check green

### M8 — Documentation & Tracker Updates (Planned)
- [x] Update `docs/frontend/data-access.md` and `docs/trackers/` with milestone status.
- [x] UX notes for new controls/attachments in feature constants where applicable.
- [x] Final audit: all checkboxes completed, sign-offs recorded.
- Sign-off: ✅

### Open UX/IA Follow-ups (Added 2025-11-28)
- [x] Surface new routes in primary nav: add `/workflows` and `/ops/storage` to `buildPrimaryNav`/`AppSidebar` so pages are discoverable (web-app/app/(app)/layout.tsx).
- [x] Workflows streaming integration: wire `runWorkflowStream` to populate `streamEvents` and show success/output states (WorkflowsWorkspace.tsx).
- [x] Standardize workflows controls on design system: replace bespoke buttons/checkbox with `Button` + `Checkbox`/`Switch` (WorkflowList.tsx, WorkflowRunPanel.tsx, mock CTA).
- [x] Restore containers tab accessibility in Agents: use `TabsTrigger` for the containers view instead of custom pills and include it in `TabsList` (AgentWorkspace.tsx).
- [x] Fix vector store file actions: per-file delete/detach handler and relabel buttons; keep store deletion at store-level (StorageAdmin.tsx).
Sign-off: ✅ UX/IA follow-ups completed (2025-11-28)

## Definition of Done
- All M1–M3 tasks complete with passing `pnpm lint` and `pnpm type-check`.
- Chat flows render attachments and structured output without regressions; streaming tolerant to new fields.
- Storage/vector/container/workflow feature scaffolds merged or explicitly deferred with rationale in this tracker.
- Tracker updated with sign-offs per phase; no open high-severity issues.

## Risk/Notes
- Attachment URLs rely on storage presign validity; add UX for expired links.
- Avoid pragmatic coupling: keep feature logic within `features/*`, data layer in `lib/*`, UI primitives in `components/ui`.
- No feature flags; ship defaults hardened for pre-GA.
