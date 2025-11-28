# Milestone: Workflows UI & Client Wiring

Status: Planned  
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
