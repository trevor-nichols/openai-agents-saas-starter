# Frontend Data Access Guidelines

_Last updated: November 10, 2025_

This document codifies how the Next.js frontend talks to the FastAPI backend. Every new feature must follow this layering to keep auth boundaries clear, maximize reuse, and make it obvious where to plug in caching, logging, or mocks.

## Layered Architecture

1. **Generated SDK (`agent-next-15-frontend/lib/api/client`)**  
   - Auto-generated via HeyAPI.  
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
   - Map SDK types into domain DTOs defined in `agent-next-15-frontend/types/*`.  
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
   - Reuse shared types from `agent-next-15-frontend/types`.

5. **Update docs/tests**  
   - Add any domain-specific notes here or in `docs/<domain>/`.  
   - Cover fetch helpers with unit tests or integration tests where it adds value.

## Streaming Guidance

- Server-only streaming (e.g., chat) should use helpers under `lib/server/streaming/*`, which call the corresponding service and yield parsed chunks. Server actions can then yield directly to UI consumers.  
- Browser-accessible streams (billing events, chat fallback) live behind `/app/api/...` proxy routes that pipe the SSE response and enforce cookie auth.  
- Client-side streaming utilities (`lib/api/streaming.ts`) only talk to our API routes to avoid leaking tokens.

## Chat Data Flow

The chat experience combines TanStack Query with an orchestrator hook so UI components stay presentation-only.

1. **Client fetch helpers**  
   - `lib/api/chat.ts` provides `sendChatMessage` and `streamChat`.  
   - Helpers emit structured errors (`ChatApiError`) and environment-gated debug logs.

2. **TanStack query integration**  
   - `lib/queries/chat.ts` wraps `sendChatMessage` with optimistic cache invalidation.  
   - `lib/queries/conversations.ts` owns list/detail keys; detail queries are prefetched any time a conversation is opened or messages stream.

3. **Controller hook**  
   - `lib/chat/useChatController.ts` handles message streaming, fallback to mutation, deletion, and agent selection state.  
   - Consumers (e.g., `app/(agent)/page.tsx`) only read the controller output, keeping UI files <200 lines.

4. **Testing**  
   - Unit tests live under `lib/api/__tests__/chat.test.ts`, `lib/chat/__tests__/useChatController.test.tsx`, and the SSE integration smoke `lib/chat/__tests__/useChatController.integration.test.tsx`.  
   - Run `pnpm vitest run` to execute the suite; add new tests near the code they validate.

5. **Debug logging**  
   - `console.debug` statements are wrapped in `NODE_ENV !== 'production'` guards to aid local troubleshooting without polluting prod logs.

When extending the chat domain, follow the same pattern: update helpers/hooks, keep controller logic pure, and document cache impacts in this section.

## Conversations Archive Flow

1. **List view** – `features/conversations/ConversationsHub.tsx` consumes `useConversations()` (TanStack Query) to fetch `/api/conversations`. Local search filters the cached list client-side, and each row prefetches its detail query for snappy drawers.
2. **Detail drawer** – `ConversationDetailDrawer` calls `useConversationDetail(conversationId)` which wraps `fetchConversationHistory` (`/api/conversations/{id}`) and caches the transcript. The drawer exposes JSON export placeholders, ID/message copy actions, and delete flows that invalidate both the list cache and the selected detail query.
3. **Deleting** – `deleteConversationById` hits the DELETE route, and the drawer invokes `removeConversationFromList` (from the list hook) so TanStack caches stay consistent without refetching the whole table.
4. **Exports** – Until the backend delivers CSV/PDF, the drawer generates a JSON blob for quick downloads; once servers are ready we can swap the handler to call `/api/conversations/{id}/export` without touching UI code.

This layering keeps the archive UX responsive and predictable, and the same hooks can be reused by upcoming admin/audit surfaces.

## Agent Catalog Flow

1. **Server services** – `lib/server/services/agents.ts` and `tools.ts` wrap the OpenAI Agents API so Next.js routes call FastAPI via the shared `getServerApiClient()` helper.
2. **API routes** – `/app/api/agents` + `/app/api/tools` proxy the services and normalize `{ success, data }` payloads for the browser.
3. **Client helpers** – `lib/api/agents.ts`/`tools.ts` fetch the App Router routes, throw descriptive errors, and keep responses typed via `types/agents.ts` + `types/tools.ts`.
4. **Query layer** – `useAgents()` + `useTools()` (TanStack Query) provide cached data, loading/error flags, and refetch methods.
5. **Feature UI** – `features/agents/AgentsOverview.tsx` renders the catalog using `GlassPanel` cards with status badges, last heartbeat, and tool lists. Rows stay keyboard-accessible, and shared toasts handle refresh/export states.

This layering mirrors the conversations stack, so future agent detail pages can reuse the same hooks without touching UI components.

## Auth Boundary Rules

- Only code in `lib/server/**` or Next.js server actions may touch Next `cookies()` or create SDK clients.  
- Client components and hooks must call `/app/api` routes or server actions—never `fetch(API_BASE_URL)` directly.  
- Any new route that returns `{ success, ... }` must populate a helpful `error` string for UI surfacing.

## Checklist for Contributors

- [ ] Service created/updated with full type coverage.  
- [ ] Optional API route added for browser access.  
- [ ] Fetch helper + hook implemented using centralized query keys.  
- [ ] Types declared under `agent-next-15-frontend/types`.  
- [ ] Documentation (this file + AGENTS.md note) updated.  
- [ ] `pnpm lint`, `pnpm type-check`, and `pnpm vitest run` executed locally.

Following this blueprint keeps the frontend predictable, auditable, and testable as we add more domains.
