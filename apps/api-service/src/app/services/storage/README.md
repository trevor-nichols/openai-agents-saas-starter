# Storage service

Tenant-scoped object storage orchestration that fronts the provider (MinIO, GCS, or in-memory), enforces upload guardrails, and persists metadata in Postgres so the rest of the app can reason about files.

## What it owns
- Presigned flows: `create_presigned_upload` and `get_presigned_download` generate signed URLs with TTL (`storage_signed_url_ttl_seconds`) and record basic activity events.
- Direct writes: `put_object` stores small server-side assets (e.g., generated images) without a presign round trip.
- Metadata persistence: buckets + objects are recorded in Postgres (`storage_buckets`, `storage_objects`) with tenant isolation, filenames, mime, size, and optional conversation/agent metadata.
- Guardrails: enforces allowed MIME types (`storage_allowed_mime_types`) and max size (`storage_max_file_mb`), sanitizes filenames, and ensures per-tenant bucket naming (`<prefix>-<tenant>` unless `GCS_BUCKET` is set).
- Observability: emits metrics per storage operation and best-effort activity events for uploads/deletes; `/health/storage` exposes provider health.

## Key pieces
- `StorageService` (`service.py`): façade used by API routes and agent helpers; coordinates provider ops, bucket creation, and persistence.
- `StorageRepository` (`infrastructure/persistence/storage/postgres.py`): Postgres CRUD for buckets/objects.
- Provider registry (`infrastructure/storage/registry.py`): resolves `StorageProviderProtocol` for `memory`, `minio` (S3-compatible), or `gcs`, caching the instance.
- Providers:
  - `MemoryStorageProvider`: test/local, non-persistent.
  - `MinioStorageProvider`: uses boto3 against MinIO/S3.
  - `GCSStorageProvider`: uses google-cloud-storage with V4 signed URLs.
- API surface: `api/v1/storage/router.py` exposes:
  - `POST /storage/objects/upload-url` (admin/owner) → presigned PUT
  - `GET /storage/objects` (viewer+) → list with pagination
  - `GET /storage/objects/{id}/download-url` (viewer+) → presigned GET
  - `DELETE /storage/objects/{id}` (admin/owner) → provider delete + soft-delete metadata

## Where it is used
- Agent attachments: `services/agents/attachments.py` and `image_ingestor.py` persist tool outputs via `put_object`, then presign for chat history rendering.
- Asset catalog: `services/assets/service.py` records generated assets in `agent_assets`, linking storage objects back to conversations/messages and powering `/api/v1/assets` listings.
- Conversation query wiring: `bootstrap/container.py` wires `AttachmentService` with `StorageService` for history/attachments.
- Health/info: `/health/storage` calls `StorageService.health_check` to report provider status without gating readiness.
- API consumers (frontend/SDK) rely on presign endpoints; there is no webhook to flip `pending_upload` → `ready`, so clients use the presigned location directly after upload.

## Configuration knobs (Settings)
- Provider selection: `STORAGE_PROVIDER` = `memory` (default), `minio`, or `gcs`.
- Bucket naming: `storage_bucket_prefix` (default `agent-data`); when `STORAGE_PROVIDER=gcs` and `GCS_BUCKET` is set, that bucket is reused (no auto-create).
- Presign TTL: `storage_signed_url_ttl_seconds` (default 900s).
- Size/MIME limits: `storage_max_file_mb` and `storage_allowed_mime_types` (see `core/settings/storage.py`).
- MinIO: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_REGION`, `MINIO_SECURE`.
- GCS: `GCS_PROJECT_ID`, `GCS_BUCKET`, `GCS_CREDENTIALS_JSON` or `GCS_CREDENTIALS_PATH`, optional `GCS_SIGNING_EMAIL`, `GCS_UNIFORM_ACCESS`.

## Developing against it
- Prefer resolving via the container (`wire_storage_service`) so the shared session factory and settings are reused; tests can inject a `MemoryStorageProvider` by setting `STORAGE_PROVIDER=memory`.
- Ensure migrations are applied (bucket/object tables) and the target bucket exists; MinIO will auto-create, GCS will not if `create_if_missing=False` is set by config.
- When adding new flows, reuse `StorageService` guardrails for MIME/size and bucket naming rather than calling providers directly.
- For server-generated assets, call `put_object`; for client uploads, use the presign endpoint and store the returned `object_id` alongside your domain record.
