<!-- SECTION: Metadata -->
# Milestone: Agent Input Attachments (API)

_Last updated: 2025-12-19_  
**Status:** In Progress  
**Owner:** @platform-foundations  
**Domain:** Backend  
**ID / Links:** [Docs: Agents SDK inputs], [Docs: Vector store file_search]

---

<!-- SECTION: Objective -->
## Objective

Enable the API service to accept user-provided images/files as direct agent inputs, while keeping vector-store (retrieval) uploads as an explicit, separate flow gated by agent capabilities. The outcome is a clean, auditable API that supports immediate multimodal chat inputs and optional knowledge-base ingestion without coupling the two.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Chat and workflow endpoints accept optional input attachments and pass them to the Agents SDK as `input_image` / `input_file` items.
- User-level upload flow exists for chat attachments with storage guardrails enforced.
- Vector-store upload flow exists to promote stored uploads to OpenAI File IDs and attach to vector stores (only when allowed by agent tooling).
- Vector-store uploads can be gated by agent capability (file_search + resolved vector store binding).
- Attachments are persisted on user messages with proper asset records (`source_tool=user_upload`).
- Tests cover input attachment validation and vector-store upload behavior.
- `hatch run lint` and `hatch run typecheck` pass for the API service.
- Tracker updated with phase completion and changelog.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- API request models for chat/workflow input attachments.
- User-level presigned upload endpoint for agent inputs.
- InputAttachment resolution service (storage -> presigned URL -> SDK input items).
- Runtime contract widened to accept text or input item lists.
- Vector-store “promote upload” endpoint (storage object -> OpenAI file -> attach to store).
- Backend tests for attachment handling and vector-store upload.

### Out of Scope
- Web app UI/UX changes.
- Background virus scanning / DLP.
- Cross-provider (non-OpenAI) file upload integration.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Direct inputs vs vector store uploads explicitly separated. |
| Implementation | ✅ | P1–P4 complete. |
| Tests & QA | ✅ | P1–P4 tests executed. |
| Docs & runbooks | ✅ | P1–P4 docs updated. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Direct input attachments are passed as Responses API input items (`input_image`, `input_file`) using presigned storage URLs.
- Vector-store uploads are an explicit action that produces an OpenAI File ID and attaches it to a vector store for `file_search`.
- Agent tooling gates vector-store option (agent must include `file_search`).
- New `InputAttachmentService` handles validation + input item assembly; storage and asset services remain the single sources of truth.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Direct Input Attachments

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | API | Add request models for input attachments (chat/workflow). | @platform-foundations | ✅ |
| A2 | API | Add user-level presigned upload endpoint for agent inputs. | @platform-foundations | ✅ |
| A3 | Service | Implement InputAttachmentService (storage -> SDK input items). | @platform-foundations | ✅ |
| A4 | Runtime | Widen runtime input contract (string or items). | @platform-foundations | ✅ |
| A5 | Tests | Unit tests for attachment validation/assembly. | @platform-foundations | ✅ |

### Workstream B – Vector Store Upload Flow

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | API | Add endpoint to promote storage object to OpenAI file + attach to vector store. | @platform-foundations | ✅ |
| B2 | Service | Implement storage->OpenAI file upload in vector store service/gateway. | @platform-foundations | ✅ |
| B3 | Tests | Tests for vector-store upload + attach flow. | @platform-foundations | ✅ |

### Workstream C – Agent-Gated Vector Store Upload

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Service | Add reusable agent capability + vector-store binding resolver for gating. | @platform-foundations | ✅ |
| C2 | API | Enforce agent-gated access on vector-store upload endpoint (agent_key required). | @platform-foundations | ✅ |
| C3 | Tests | Unit tests covering allow/deny cases for agent-gated uploads. | @platform-foundations | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | API design + flow separation | Tracker created, plan agreed | ✅ | 2025-12-19 |
| P1 – Direct Inputs | Chat/workflow input attachments + upload endpoint | A1–A5 complete + tests | ✅ | 2025-12-22 |
| P2 – Vector Store Upload | Storage -> OpenAI file -> attach flow | B1–B3 complete + tests | ✅ | 2025-12-23 |
| P3 – Hardening | Lint/typecheck + docs update | Green checks + tracker updated | ✅ | 2025-12-24 |
| P4 – Agent Gating | Agent-gated vector store upload flow | C1–C3 complete + tests | ✅ | 2025-12-26 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- OpenAI API key configured for file upload endpoints.
- Storage provider configured (MinIO/GCS/memory).

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Oversized/mime-invalid uploads | Med | Enforce storage guardrails at presign + input validation. |
| Leakage across tenants | High | Validate storage object tenant ownership before use. |
| Provider changes | Med | Keep provider interaction isolated in gateway/service. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test unit` (or targeted tests)
- Manual: create upload URL, upload a PNG, run chat with attachment.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No feature flags; endpoints are additive.
- Ensure `STORAGE_PROVIDER` is configured for presigned uploads in non-dev environments.
- Add documentation for new endpoints in API reference.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-19 — Milestone created; alignment captured.
- 2025-12-19 — P1 complete: direct input attachments + upload endpoint + tests + lint/typecheck.
- 2025-12-19 — P2 complete: vector-store upload endpoint + storage->OpenAI file flow + tests + lint/typecheck.
- 2025-12-19 — P3 complete: docs updated; lint/typecheck re-run.
- 2025-12-19 — P4 scoped: agent-gated vector store uploads added to plan.
- 2025-12-19 — P4 complete: agent-gated uploads implemented + tests + docs + lint/typecheck.
- 2025-12-19 — Attachment not-found now returns 404 (chat/workflows); tests added.
- 2025-12-19 — Input attachment asset creation now best-effort; reuse safe.
