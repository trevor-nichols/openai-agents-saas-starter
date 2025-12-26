# Milestone: Workflows UI & Client Wiring

Status: Done  
Owner: App Frontend  
Goal: Integrate the new workflow API surface (runs list, descriptors, cancel, enriched SSE) into the Next.js app and deliver a professional workflows UX.

## Scope & Tasks

### 1) Client wiring
- Add typed wrappers in `lib/api/workflows.ts` for:
  - `listWorkflowRunsApiV1WorkflowsRunsGet`
  - `cancelWorkflowRunApiV1WorkflowsRunsRunIdCancelPost`
  - `getWorkflowDescriptorApiV1WorkflowsWorkflowKeyGet`
- Add TanStack Query hooks in `lib/queries/workflows.ts`:
  - `useWorkflowRunsQuery` (cursor/limit aware)
  - `useCancelWorkflowRunMutation`
  - `useWorkflowDescriptorQuery`
- Update streaming handler to surface `server_timestamp` and SSE `event/id` if provided.

### 2) UI surface (features/workflows)
- Left rail: show descriptor summary (steps/stages, allow_handoff flag) when a workflow is selected.
- Main pane: add run history table (paginated/infinite scroll) with status badges, started/ended, duration, user/conv id, prompt snippet; row click opens run detail.
- Run detail panel: show steps with agent names, outputs, structured output JSON; provide “Cancel” when status is running, and “Retry” (if/when backend supports it).
- Stream log: include server timestamp in event chips; display SSE event type when present.
- Add empty/error/loading states matching component library; remove mock-only affordances when API is live (keep Simulate only when `USE_API_MOCK`).

### 3) Routing & layout
- Ensure `/workflows` page supports history/query params for selected workflow and run (e.g., `?workflow=foo&run=bar`) to allow deep links.
- Consider `ResizablePanel` for list vs detail; keep mobile stack graceful.

### 4) Testing
- Unit tests: hook/query behavior (pagination, cache keys), `WorkflowRunPanel` validation, `WorkflowStreamLog` timestamp rendering.
- Integration/E2E: happy path run + history load; cancel flow; descriptor fetch.
- Type checks: `pnpm lint` and `pnpm type-check`.

### 5) Documentation
- Update `docs/frontend/data-access.md` with new queries and wiring pattern.
- Update `docs/frontend/ui/components.md` references if new UI primitives are added.

## Definition of Done
- New API wrappers/hooks exported; no TS errors.
- `/workflows` shows live data (descriptor + run history) with cancel control; stream log shows server timestamps.
- Tests cover list pagination + cancel; Playwright adds a basic run-history check.

## UX/Interaction Direction (reference)
- Two-column resizable workspace: left rail (workflows + descriptor summary), right pane (run form, history table, live stream/log, run detail).
- URL-backed selection: `?workflow=<key>&run=<id>` drives which workflow and run are active; supports deep links/refresh.
- Run history table: status badge, started/ended, duration, user, conversation, prompt snippet; filters (workflow/status/date/conversation); infinite scroll via cursor.
- Run detail: step cards with agent names, timing, outputs/structured JSON; action bar with Cancel when running; Retry when supported by backend.
- Stream log: show SSE event type, server timestamp, terminal highlight; only displays events for the active run.
- Mobile: stacked sections; table degrades to cards; actions remain accessible.

## Execution Order
1) Client layer: add wrappers + queries; export in barrels.
2) URL state + filters: wire workflow/run selection and filters to query params.
3) History table + detail pane + cancel action; ensure cache invalidation.
4) Stream log polish: render server timestamps + event types.
5) Responsive/empty/error/loading polish.
6) Tests + docs; `pnpm lint && pnpm type-check`.

## Sign-off Notes
- Update “Status” as phases complete (Planned → In Progress → Done).
- For each phase: code merged, tests updated/green, docs touched where relevant.

### Progress log
- [x] Client wiring (wrappers + queries, SSE timestamp support)
- [x] URL-backed selection, history table, run detail with cancel
- [x] Stream log polish/responsiveness (server timestamp + event label)
- [x] Tests + docs, final lint/type-check pass
