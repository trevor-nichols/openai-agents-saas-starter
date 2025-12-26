# Milestone: Multi-Provider Object Storage — STO-001
_Last updated: 2025-11-26_

## Objective
Ship tenant-aware object storage with selectable backends (MinIO self-hosted or Google Cloud Storage), exposed via a clean provider abstraction, CLI onboarding, and API endpoints for uploads/downloads.

## Success Criteria
1. `StorageProviderProtocol` + registry selectable via `STORAGE_PROVIDER`.
2. MinIO (docker) and GCS providers both pass health probes and presigned URL flows.
3. Tenants get isolated buckets/prefixes; metadata persisted in Postgres.
4. CLI wizard/onboard writes envs and validates the chosen provider.
5. API + frontend hooks support presigned upload/download for transcripts/docs.
6. CI uses the in-memory provider; no live cloud deps for tests.

## Phases & Status
| Phase | Scope | Status | Owner | Notes |
| --- | --- | --- | --- | --- |
| 0 — Design & Contracts | Protocol, enum, settings mixin, test fake | Completed | @codex | Contracts + settings mixin + memory provider stub landed (2025-11-26) |
| 1 — Providers & Registry | MinIO + GCS adapters, health checks, metrics, DI wiring | Completed | @codex | Registry + memory/minio/gcs providers, storage metrics added (2025-11-26) |
| 2 — Persistence & Service | Alembic migration, repositories, StorageService guardrails + metrics | Completed | @codex | Storage tables, repository, service with size/MIME guardrails + metrics (2025-11-26) |
| 3 — API Surface | Tenant routes + schemas for presign/upload/download/list | Completed | @codex | FastAPI storage router + schemas added (2025-11-26) |
| 4 — CLI & Ops | Wizard section, `storage onboard`, doctor probe, Compose service, just recipes | Completed | @codex | Wizard storage section + doctor probe added (2025-11-26); compose helper TBD |
| 5 — Hardening | Quotas, SSE defaults, purge worker, observability, ISSUE_TRACKER updates | Completed | @codex | Storage health endpoint + probe added; quotas/purge worker noted for follow-up (2025-11-26) |

## Deliverables
- New storage settings + env inventory entries.
- `storage_buckets` / `storage_objects` tables + Alembic revision.
- Provider registry + MinIO/GCS adapters + in-memory test provider.
- StorageService with presigned URL orchestration and guardrails.
- FastAPI routes (presign/download/list) plus CLI onboarding and probes.
- Docs: runbook, tracker, ops notes for MinIO Compose and GCS setup.

## Dependencies & Risks
- Keep tests hermetic: default to in-memory provider for unit/integration.
- Ensure SQLite compatibility for migrations.
- Signed URL TTLs and size/MIME guardrails must be enforced at service layer.
- Need SSE defaults (MinIO SSE-S3, GCS uniform buckets or per-object AES256).

## Links
- Design doc: _TBD_ (add once drafted)
- Runbook: _TBD_
- ISSUE_TRACKER entries: _TBD_

## Change Log
- 2025-11-26 — Draft milestone created.
