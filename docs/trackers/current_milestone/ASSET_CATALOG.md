<!-- SECTION: Metadata -->
# Asset Catalog — Generated Files & Images

_Last updated: 2025-12-19_  
**Status:** Completed  
**Owner:** Platform Foundations  
**Domain:** Cross-cutting (Backend + Frontend)  
**ID / Links:** [Storage service](../../apps/api-service/src/app/services/storage/README.md), [Attachments](../../apps/api-service/src/app/services/agents/attachments.py)

---

<!-- SECTION: Objective -->
## Objective

Provide a first-class, queryable asset catalog for generated images and files that is tenant-scoped, auditable, and linkable back to conversations/messages, plus a polished Asset Library UI for browsing, filtering, downloading, and deleting assets.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- New `agent_assets` table with indexed metadata and FK to `storage_objects`.
- Assets are created for `image_generation` outputs and Code Interpreter container file citations.
- Asset records are linkable to conversations and, when possible, to the specific message.
- New API endpoints: list/filter assets, fetch details, delete, and presign download.
- OpenAPI updated + frontend client regenerated (if schemas change).
- Tests cover asset creation, list filtering, and delete flows.
- `hatch run lint` and `hatch run typecheck` are green.
- Frontend Asset Library page (tabs for images/files) live under authenticated app shell.
- Frontend uses BFF API routes + fetch helpers + TanStack Query hooks (no direct backend calls).
- UX supports filtering by conversation/source/tool, download, and delete.
- `pnpm lint` and `pnpm type-check` are green.
- Docs/trackers updated.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Backend data model for assets (`agent_assets`).
- Asset ingestion on tool outputs (image_generation + code_interpreter).
- Asset listing/filtering and download/delete APIs.
- Storage object ↔ asset linkage and metadata propagation.
- Optional message linkage (message_id) to support deep links from asset to chat.
- Frontend Asset Library (single page with tabs for Images / Files) and supporting data-access layers.
- BFF asset proxy routes + client fetch helpers + TanStack Query hooks.
- High-end, accessible UI using existing Shadcn primitives + design system.

### Out of Scope
- Retention policies or lifecycle jobs for storage providers.
- Billing/usage accounting for assets.
- Backfill of historical assets (optional follow-up if needed).
- Bulk download/delete, sharing links, or advanced tagging.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Backend done; frontend design + UX plan in scope. |
| Implementation | ✅ | Backend + frontend Asset Library implemented. |
| Tests & QA | ✅ | Backend + frontend tests green with lint/type-check. |
| Docs & runbooks | ✅ | Milestone and UX notes updated. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Introduce `agent_assets` as a dedicated domain model, avoiding overloading `storage_objects`.
- Assets reference `storage_objects` (FK) and include `asset_type`, `source_tool`, `conversation_id`, `message_id`, `tool_call_id`, `response_id`, and optional `container_id` / `openai_file_id`.
- Ingestion occurs in `AttachmentService` after storage writes; `IngestedImage` and `IngestedContainerFile` already surface `storage_object_id` for linkage.
- Message linkage: update message persistence (`persist_assistant_message`) to return message id and/or provide a follow-up association method to attach assets to the message once it is persisted.
- New API module: `api/v1/assets/` with list/detail/delete/download endpoints (tenant-scoped, role-gated).
- Keep storage deletion as the single source of truth; asset deletion should cascade/soft-delete the storage object and mark asset deleted.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Data Model & Migrations

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | DB | Add `agent_assets` table + indexes (tenant_id, asset_type, conversation_id, message_id, created_at). | Platform Foundations | ✅ |
| A2 | DB | Add FK to `storage_objects` and optional FKs for `agent_messages` / `agent_conversations`. | Platform Foundations | ✅ |
| A3 | DB | Alembic migration via `just migration-revision ...` and `just migrate`. | Platform Foundations | ✅ |

### Workstream B – Services & Ingestion

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Service | Create `AssetService` + repository for CRUD/listing. | Platform Foundations | ✅ |
| B2 | Ingest | On image_generation ingest, create `agent_assets` row linked to storage object. | Platform Foundations | ✅ |
| B3 | Ingest | On container file ingest, create `agent_assets` row with container/file ids. | Platform Foundations | ✅ |
| B4 | Linkage | Update message persistence to associate assets with `message_id`. | Platform Foundations | ✅ |

### Workstream C – API & Contracts

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | API | Add `api/v1/assets` router: list, detail, delete, download-url. | Platform Foundations | ✅ |
| C2 | API | Add filters: asset_type, conversation_id, agent_key, created_after, mime_prefix. | Platform Foundations | ✅ |
| C3 | OpenAPI | Regenerate OpenAPI + TS client fixtures if schemas changed. | Platform Foundations | ✅ |

### Workstream D – Tests & Docs

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Tests | Unit/integration tests for asset ingestion + list filters. | Platform Foundations | ✅ |
| D2 | Tests | API tests for download/delete flows. | Platform Foundations | ✅ |
| D3 | Docs | Update storage/attachments docs with asset catalog usage. | Platform Foundations | ✅ |

### Workstream E – Frontend Data Access

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| E1 | BFF | Add `/app/api/v1/assets` proxy routes (list/detail/delete/download-url). | Platform Foundations | ✅ |
| E2 | Client | Add `lib/api/assets.ts` + error handling. | Platform Foundations | ✅ |
| E3 | Queries | Add query keys + TanStack Query hooks for assets. | Platform Foundations | ✅ |

### Workstream F – Frontend UX

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| F1 | Page | Add `/assets` page under app shell + nav entry. | Platform Foundations | ✅ |
| F2 | UI | Asset Library orchestrator + filters + tabs (images/files). | Platform Foundations | ✅ |
| F3 | UI | Image gallery + file table + actions (download/delete). | Platform Foundations | ✅ |
| F4 | QA | UI tests for filters/actions + states. | Platform Foundations | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | Schema + API shape agreed | Finalized design + migration plan | ✅ | 2025-12-19 |
| P1 – Implementation | Workstreams A–C2 | Assets persisted + APIs live | ✅ | 2025-12-19 |
| P2 – Validation | Workstream D + QA | Tests + docs green | ✅ | 2025-12-19 |
| P3 – Contracts | Workstream C3 | OpenAPI + HeyAPI artifacts regenerated | ✅ | 2025-12-19 |
| P4 – Frontend Plumbing | Workstream E | BFF + client helpers + queries | ✅ | 2025-12-19 |
| P5 – Frontend UX | Workstream F1–F3 | Asset Library UI complete | ✅ | 2025-12-19 |
| P6 – Frontend QA | Workstream F4 | UI tests + lint/type-check green | ✅ | 2025-12-19 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Storage service (`apps/api-service/src/app/services/storage/service.py`) and attachments pipeline.
- Conversation message persistence (`apps/api-service/src/app/infrastructure/persistence/conversations/*`).
- OpenAPI export + frontend client regeneration flow (if API changes).
- Frontend data-access layering (`docs/frontend/data-access.md`).
- Existing UI primitives (`apps/web-app/components/ui/*`).

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Message linkage requires API changes | Med | Add a minimal `message_id` return or post-write association step. |
| Asset deletion semantics unclear | Med | Define delete = soft-delete asset + delete storage object. |
| Filtering on JSON metadata | Low | Keep core filters as indexed columns in `agent_assets`. |
| Migration conflicts (multi-head) | Med | Use `just migration-revision` + `alembic upgrade heads`. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test` (or scoped tests)
- `cd apps/web-app && pnpm lint`
- `cd apps/web-app && pnpm type-check`
- `cd apps/web-app && pnpm vitest run` (targeted UI tests)
- Validate list/download/delete endpoints via API tests or smoke requests.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Apply DB migration via `just migrate`.
- No feature flags; endpoints available once migration lands.
- If backfill is needed, add a one-off script to create assets for existing storage objects with metadata.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-19 — Created milestone for asset catalog plan and scope.
- 2025-12-19 — Implemented asset model/migration, ingestion + linkage, and assets API; lint/typecheck green.
- 2025-12-19 — Added API route tests for asset download/delete flows.
- 2025-12-19 — Documented asset catalog service and storage integration.
- 2025-12-19 — Signed off P1 (implementation) and P2 (validation); tests green.
- 2025-12-19 — Regenerated OpenAPI fixtures + HeyAPI client; milestone complete.
- 2025-12-19 — Aligned conversation UUID coercion for asset ingestion; added unit coverage.
- 2025-12-19 — Accepted non-UUID conversation_id filter for assets + regenerated SDK.
- 2025-12-19 — Map missing storage objects to 404 for asset downloads; add service test.
- 2025-12-19 — Make asset linking best-effort for agents/workflows; add unit coverage.
- 2025-12-19 — Expanded milestone to include frontend Asset Library delivery.
- 2025-12-19 — Completed frontend plumbing (BFF routes, fetch helpers, queries) + API route tests.
- 2025-12-19 — Added Asset Library shell page + nav entry scaffold.
- 2025-12-19 — Implemented Asset Library UX (filters, tabs, gallery/table, actions) + frontend tests.
- 2025-12-19 — Corrected assets BFF 404 handling for missing assets/download URLs + tests.
