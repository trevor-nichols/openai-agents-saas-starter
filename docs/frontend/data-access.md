# Frontend Data Access Guidelines

_Last updated: November 10, 2025_

This document codifies how the Next.js frontend talks to the FastAPI backend. Every new feature must follow this layering to keep auth boundaries clear, maximize reuse, and make it obvious where to plug in caching, logging, or mocks.

## Layered Architecture

1. **Generated SDK (`web-app/lib/api/client`)**  
  - Auto-generated via HeyAPI against the committed billing-on spec `../api-service/.artifacts/openapi.json` (see `openapi-ts.config.ts`).  
   - Never imported directly from React components.  
   - Only server-side services may create SDK clients, typically via `lib/server/apiClient.ts`.

2. **Server Services (`lib/server/services/*`)**  
   - Wrap SDK calls per domain (auth, billing, chat, tools, conversations, …).  
   - Responsible for attaching auth, mapping backend payloads into frontend-friendly shapes, and handling mock mode.  
   - All server actions and API routes call services, never the SDK or `fetch` directly.

3. **Server Actions / API Routes (`app/api/**`, `app/(agent)/actions.ts`, etc.)**  
   - Translate HTTP semantics (status codes, SSE piping) and marshal data for the browser.  
   - Routes are only created when the browser must call the backend (e.g., TanStack Query, SSE).  
   - Server components or actions may call services directly when the client never needs the data.

4. **Client Fetch Helpers (`lib/api/*.ts`)**  
   - Tiny wrappers that call our API routes (`/api/...`) and throw typed errors.  
   - Provide test seams for hooks and components.

5. **TanStack Query Hooks (`lib/queries/*.ts`)**  
   - Always import fetch helpers + centralized keys (`lib/queries/keys.ts`).  
   - Expose `isLoading`, `error`, `refetch` for consistent UX.  
   - Set sensible `staleTime` per domain (streams: 0, lists: minutes).  
   - Non-React consumers should reuse the fetch helpers.

## Building a New Data Flow

1. **Add/extend a server service**  
   - Use `getServerApiClient()` to enforce cookie-based auth.  
   - Map SDK types into domain DTOs defined in `web-app/types/*`.  
   - Handle mock mode if relevant (`USE_API_MOCK`).

2. **Expose the service**  
   - Prefer server actions when only server components need the data.  
   - Add an `/app/api/...` route when browser code (React Query, SSE, file downloads) must call it.  
   - Keep handlers <50 lines; delegate to services for business logic.

3. **Create a client fetch helper**  
   - Lives under `lib/api/*.ts`.  
   - Calls the API route, parses JSON, throws descriptive errors if `success` is false.

4. **Add query keys & hooks**  
   - Register keys in `lib/queries/keys.ts`.  
   - Create a hook in `lib/queries/<domain>.ts`.  
   - Return `{ dataAlias, isLoading, error, refetch }`.  
   - Reuse shared types from `web-app/types`.

5. **Update docs/tests**  
- Add any domain-specific notes here or in `docs/<domain>/`.  
- Cover fetch helpers with unit tests or integration tests where it adds value.

## Contact form

- Flow: client form ➜ `/app/api/contact` ➜ `lib/server/services/marketing.submitContact` ➜ FastAPI `POST /api/v1/contact`.
- UI calls `useSubmitContactMutation` (TanStack Query) which wraps `lib/api/contact.submitContactRequest`.
- The backend endpoint is unauthenticated; we still gate spam with a honeypot field.

### Choosing Between Server Services and `/api` Fetchers

- **Server components/actions** call domain services directly. Example: server actions in the chat workspace invoke `lib/server/services/chat.ts` so the SDK never leaks to the browser.  
- **Browser code (React Query, plain hooks, client components)** must call `/app/api/...` routes via fetch helpers under `lib/api/*`. Never import `lib/server/**` modules or `getServerApiClient()` from the browser bundle—those files include `use server` directives and will crash the build.  
- When a feature has both server and browser consumers, expose it twice:
  - Keep the domain service for server-side orchestration.
  - Add a lightweight API route + fetch helper for browser access.  
- Example: billing subscription flows now share `lib/api/billingSubscriptions.ts`, and `lib/queries/billingSubscriptions.ts` exclusively calls those helpers. Server components that need the same data can still import `lib/server/services/billing.ts`.  
- Billing visibility: `NEXT_PUBLIC_ENABLE_BILLING` (default `false`) controls nav/pages/API routes/query `enabled` flags. The Starter Console writes it to `apps/web-app/.env.local` alongside backend `ENABLE_BILLING` in `apps/api-service/.env.local`.
- If a hook only ever runs in a server component, prefer a server action instead of creating a redundant `/api` route.

## Streaming Guidance

- Server-only streaming (e.g., chat) should use helpers under `lib/server/streaming/*`, which call the corresponding service and yield parsed chunks. Server actions can then yield directly to UI consumers.  
- Browser-accessible streams (billing events, chat fallback) live behind `/app/api/...` proxy routes that pipe the SSE response and enforce cookie auth.  
- Client-side streaming utilities (`lib/api/streaming.ts`) only talk to our API routes to avoid leaking tokens.
- Hooks exposed to client components must come from `lib/queries/*`. For example, import `useBillingStream` from `lib/queries/billing` and `useSilentRefresh` from `lib/queries/session`; the legacy `hooks/*` versions have been removed to keep a single source of truth.

## Chat Data Flow

The chat experience combines TanStack Query with an orchestrator hook so UI components stay presentation-only.

1. **Client fetch helpers**  
   - `lib/api/chat.ts` provides `sendChatMessage` and `streamChat`.  
   - Helpers emit structured errors (`ChatApiError`) and environment-gated debug logs.

2. **TanStack query integration**  
   - `lib/queries/chat.ts` wraps `sendChatMessage` with optimistic cache invalidation.  
   - `lib/queries/conversations.ts` owns list/detail keys; detail queries are prefetched any time a conversation is opened or messages stream.

3. **Controller hook**  
   - `lib/chat/controller/useChatController.ts` handles message streaming, fallback to mutation, deletion, and agent selection state.  
   - Consumers (e.g., `app/(agent)/page.tsx`) only read the controller output, keeping UI files <200 lines.

4. **Testing**  
   - Unit tests live under `lib/api/__tests__/chat.test.ts`, `lib/chat/__tests__/useChatController.test.tsx`, and the SSE integration smoke `lib/chat/__tests__/useChatController.integration.test.tsx`.  
   - Run `pnpm vitest run` to execute the suite; add new tests near the code they validate.

5. **Debug logging**  
   - `console.debug` statements are wrapped in `NODE_ENV !== 'production'` guards to aid local troubleshooting without polluting prod logs.

When extending the chat domain, follow the same pattern: update helpers/hooks, keep controller logic pure, and document cache impacts in this section.

## Workflows

- API wrappers: `lib/api/workflows.ts` (list, run, run-stream, run detail, list runs, descriptor, cancel) with `USE_API_MOCK` support and streaming parser.
- Queries: `lib/queries/workflows.ts`:
  - `useWorkflowsQuery()` — list available workflows.
  - `useWorkflowDescriptorQuery(workflowKey)` — fetch descriptor (stages/steps/handoffs).
  - `useWorkflowRunsQuery(filters)` — list runs with cursor pagination and filters.
  - `useWorkflowRunQuery(runId)` — run detail.
  - `useRunWorkflowMutation()` — start a run.
  - `useWorkflowStream(...)` — async generator yielding streaming events.
  - `useCancelWorkflowRunMutation()` — cancel a running workflow.
- Feature UI: `features/workflows/WorkflowsWorkspace.tsx` with list + descriptor summary, run form, run history table, run detail (with cancel), and streaming log (`WorkflowStreamLog`).
- Mock stream trigger remains available when `USE_API_MOCK` to exercise the UI without backend SSE.

## Storage

- Storage objects: `lib/api/storageObjects.ts`; presign download proxy in `app/api/storage/objects/[objectId]/download-url/`.
- Queries: `lib/queries/storageObjects.ts`.
- UI: `features/storage/StorageAdmin.tsx` (admin surface; mock-friendly).
- Chat attachments resolve download URLs via the proxy; UI shows errors and allows manual fetch if presign is missing/expired.

## Vector Stores

- API wrappers: `lib/api/vectorStores.ts` (list/create/delete, file attach/list/delete, search) with `USE_API_MOCK` scaffolds.
- Queries: `lib/queries/vectorStores.ts`.
- UI: managed from `features/storage/StorageAdmin.tsx` for now (admin-facing).

## Containers

- API wrappers: `lib/api/containers.ts` (list/create/delete, bind/unbind agent→container) with mock support.
- Queries: `lib/queries/containers.ts`.
- UI: Agents workspace containers tab (`features/agents/AgentWorkspace.tsx` + `ContainerBindingsPanel`) for binding the selected agent to a container.

## Conversations Archive Flow

1. **List view** – `features/conversations/ConversationsHub.tsx` consumes `useConversations()` (TanStack Query) to fetch `/api/conversations`. Local search filters the cached list client-side, and each row prefetches its detail query for snappy drawers.
2. **Detail drawer** – `ConversationDetailDrawer` calls `useConversationDetail(conversationId)` which wraps `fetchConversationHistory` (`/api/conversations/{id}`) and caches the transcript. The drawer exposes JSON export, ID/message copy actions, and delete flows that invalidate both the list cache and the selected detail query.
3. **Deleting** – `deleteConversationById` hits the DELETE route, and the drawer invokes `removeConversationFromList` (from the list hook) so TanStack caches stay consistent without refetching the whole table.
4. **Exports** – The drawer currently generates a JSON export in-browser. If server-side exports are introduced, route the handler through `/api/conversations/{id}/export` and keep the UI contract stable.

This layering keeps the archive UX responsive and predictable, and the same hooks can be reused by admin/audit surfaces.

### Conversation Events

- Flow: `fetchConversationEvents` → `/app/api/conversations/[conversationId]/events` → `getConversationEvents` service → FastAPI `GET /api/v1/conversations/{id}/events`.
- Default `mode` is `transcript`; pass `mode=full` plus optional `workflow_run_id` for audit-grade detail (tool calls, reasoning, outputs).
- Hook: `useConversationEvents(conversationId, { mode, workflowRunId })` returns cached event logs; history remains available as a fallback while UI migrates to events.

## Agent Catalog Flow

1. **Server services** – `lib/server/services/agents.ts` and `tools.ts` wrap the OpenAI Agents API so Next.js routes call FastAPI via the shared `getServerApiClient()` helper.
2. **API routes** – `/app/api/agents` + `/app/api/tools` proxy the services and normalize `{ success, data }` payloads for the browser.
3. **Client helpers** – `lib/api/agents.ts`/`tools.ts` fetch the App Router routes, throw descriptive errors, and keep responses typed via `types/agents.ts` + `types/tools.ts`.
4. **Query layer** – `useAgents()` + `useTools()` (TanStack Query) provide cached data, loading/error flags, and refetch methods.
5. **Feature UI** – `features/agents/AgentsOverview.tsx` renders the catalog using `GlassPanel` cards with status badges, last heartbeat, and tool lists. Rows stay keyboard-accessible, and shared toasts handle refresh/export states.

This layering mirrors the conversations stack and should be reused for agent detail pages to avoid duplicating hooks.

## Auth Boundary Rules

- Only code in `lib/server/**` or Next.js server actions may touch Next `cookies()` or create SDK clients.  
- Client components and hooks must call `/app/api` routes or server actions—never `fetch(API_BASE_URL)` directly.  
- Any new route that returns `{ success, ... }` must populate a helpful `error` string for UI surfacing.

## Checklist for Contributors

- [ ] Service created/updated with full type coverage.  
- [ ] Optional API route added for browser access.  
- [ ] Fetch helper + hook implemented using centralized query keys.  
- [ ] Types declared under `web-app/types`.  
- [ ] Documentation (this file + AGENTS.md note) updated.  
- [ ] `pnpm lint`, `pnpm type-check`, and `pnpm vitest run` executed locally.

## Shared UI Helpers

- **Global toast provider** – `app/providers.tsx` mounts the single `Toaster` instance from `components/ui/sonner` (styled with the graphite palette). Always import `useToast` from `components/ui/use-toast` inside feature code so every success/error loop routes through the same provider (avoid importing `sonner` directly in components).  
- **Data table kit** – `components/ui/data-table` wraps `@tanstack/react-table` with consistent column rendering, skeleton/error states, pagination controls, and optional row callbacks. Pass your `ColumnDef<T>` array, data slice, and shared `EmptyState` or `ErrorState`, then render the resulting rows inside the authenticated shell. Use `DataTable` + `DataTablePagination` (or disable pagination for filtered archives) so conversations/billing/account tables share the same layout, keyboard handling, and toast-quality messaging.

Following this blueprint keeps the frontend predictable, auditable, and testable as we add more domains.
