# Milestone: Conversation Search & Pagination (Backend + Frontend)

Status: In Progress (backend + API + frontend plumbing merged; metrics/tests pending)
Owner: Platform Foundations
Goal: Ship production-grade conversation listing and search (Postgres full-text), with pagination and frontend UX wiring. pgvector/semantic search is explicitly out-of-scope for this milestone.

## Phases

### Phase 1 — Backend foundations
- Add Alembic migration: generated `text_tsv` column on `agent_messages`, GIN index, optional filter index `(tenant_id, agent_entrypoint, updated_at)`.
- Extend `ConversationRepository` contract for keyset pagination and SQL full-text search (returns score + latest message preview).
- Implement Postgres repo changes: keyset pagination on `(updated_at DESC, id DESC)`, full-text search via `plainto_tsquery('english', :q)` grouped by conversation.
- Update service layer to use repository search (remove in-memory scan), add preview trimming, enforce tenant scope.
- API: add `limit`/`cursor` to list endpoint; introduce `GET /api/v1/conversations/search` with query, limit, cursor, optional filters; return `{items, next_cursor}`.
- Metrics + rate limiting: emit search/list latency + result count; apply existing Redis rate limiter to search.
- Tests: unit for repo pagination + search ranking; API contract tests for list/search + error paths.

### Phase 2 — Frontend integration
- Regenerate HeyAPI SDK after API shape changes.
- Server actions: expose paginated list and search endpoints; propagate cursors.
- TanStack Query hooks: `useInfiniteQuery` for list; debounced search hook with infinite scroll.
- UI: chat/sidebar + archive panels add search input and “Recent vs Search” tabs; show loading/empty states; highlight match snippet when provided.
- Frontend tests: hook unit tests for pagination state; e2e happy path for search list + delete flow.

### Phase 3 — Operations & polish
- Add runbook entry: how to run migrations (`just migrate`), reindex tsvector, and troubleshoot slow queries.
- Observability dashboard panels for search latency, error rate, and rows scanned.
- Optional retention/archival note (soft delete or TTL job) to keep indexes small.

## Out of scope
- Semantic/vector search (pgvector); embeddings pipeline; rerankers.
- Feature flags (repo is pre-GA; ship as default behavior).

## Definition of Done
- Migrations applied; CI green (`hatch run lint && hatch run typecheck`, `pnpm lint && pnpm type-check`).
- API contract tests cover pagination and search.
- Frontend lists paginate via cursor; search works with debounce and infinite scroll; UX shows empty/error states.
- Metrics and rate limits active in staging.
