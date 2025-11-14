<!-- SECTION: Title -->
# Frontend Data Layer Milestone

<!-- SECTION: Objective -->
## Objective
Deliver a stable, fully typed data layer that the UI team can build on without refactors. This milestone locks down the chat/conversation flows, consolidates data access patterns, and documents the contracts expected by downstream consumers.

<!-- SECTION: Scope -->
## In Scope
- Consolidation of conversation and chat state into reusable hooks.
- Completion of browser-facing fetch helpers that proxy Next API routes.
- Test coverage and documentation for the data-access stack.
- Cleanup of legacy code paths that conflict with the new pattern.

<!-- SECTION: Out of Scope -->
## Out of Scope
- Any visual redesign or component styling changes.
- Shadcn component authoring or layout adjustments.
- UX polish beyond replacing ad-hoc alerts with standardized notifications.

<!-- SECTION: Deliverables -->
## Deliverables
- `useChatController` (and supporting hooks) orchestrating streaming, mutations, and optimistic updates.
- Canonical conversation hooks backed by TanStack Query only.
- Completed API helpers under `lib/api/*` for chat/conversations.
- Unit tests for critical helpers and hooks.
- Updated documentation covering the new flow.

<!-- SECTION: Workstreams -->
## Workstreams & Tasks
- **Chat Controller**
  - [x] Implement `useChatController` to encapsulate message sending, streaming, fallbacks, and conversation metadata.
  - [x] Expose a lightweight interface consumed by page-level components (messages, status flags, dispatchers).
  - [x] Add agent selection handling (selected agent id + persistence) without UI wiring.
- **Conversation Data**
  - [x] Migrate `app/(agent)/page.tsx` to consume `lib/queries/conversations` rather than the legacy hook.
  - [x] Delete `hooks/useConversations.ts` after migration and ensure no imports remain.
  - [x] Ensure detail queries (`queryKeys.conversations.detail`) are populated for history lookups.
- **API Client Helpers**
  - [x] Fill in `lib/api/chat.ts` with helpers for `/api/chat` and `/api/chat/stream` interactions.
  - [x] Standardize error objects and logging (no `alert` usage).
  - [x] Confirm fetch helpers include exhaustive type coverage using generated OpenAPI types.
- **Testing & Observability**
  - [x] Add unit tests (Vitest) for chat helpers and the controller hook (using React Testing Library + QueryClientProvider).
  - [x] Add integration smoke covering streaming fallback path (SSE fetch) to guard end-to-end flow.
  - [x] Instrument structured logging (console.debug/info) behind `NODE_ENV !== 'production'`.
- **Docs & Cleanup**
  - [x] Update `docs/frontend/data-access.md` with a “Chat Data Flow” section referencing new hooks.
  - [x] Refresh `agent-next-15-frontend/SNAPSHOT.md` once file moves are complete.
  - [x] Document testing instructions and lint/type-check expectations in this tracker.

<!-- SECTION: Milestone States -->
## Status Tracking
| Area | Status | Notes |
| ---- | ------ | ----- |
| Chat controller | ☑ Completed | Hook extracted and wired into AgentPage |
| Conversation consolidation | ☑ Completed | Page uses TanStack hook; detail cache prefetch/remove handled |
| Fetch helpers | ☑ Completed | Chat helpers implemented; error handling standardized |
| Testing | ☑ Completed | Unit + SSE integration coverage in place |
| Documentation | ☑ Completed | Data-access doc + snapshot refreshed; tracker lists required commands |

<!-- SECTION: Risks -->
## Risks & Mitigations
- **Streaming complexity:** SSE parsing and fallback logic are hard to mock. Mitigation: isolate pure helpers and unit-test them with recorded payloads.
- **Query cache churn:** Switching hooks can cause transient cache misses. Mitigation: define consistent query keys and preload history on selection.
- **Cross-team dependencies:** UI team may start early. Mitigation: publish interim hook interfaces and communicate changes via Slack + this tracker.

<!-- SECTION: Exit Criteria -->
## Exit Criteria
- All tasks above checked off and reviewed.
- `pnpm lint` and `pnpm type-check` pass without warnings.
- No references to legacy hooks or direct `/api/v1/...` browser fetches remain.
- Documentation updated and shared with UI collaborators.

