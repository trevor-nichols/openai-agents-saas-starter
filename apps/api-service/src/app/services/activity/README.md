# Activity service

Tenant-scoped audit/activity log with optional SSE streaming and per-user inbox state.

## What lives here
- `service.py` — façade that validates actions, persists events, handles inbox state (read/dismiss/mark-all), and optionally fan-outs to a stream backend.
- `registry.py` — whitelist of supported `action` strings plus allowed/required metadata keys.
- Infra: `app/infrastructure/persistence/activity/{repository,inbox_repository,models}.py` (SQLAlchemy repos + tables `activity_events`, `activity_event_receipts`, `activity_last_seen`); `app/infrastructure/activity/redis_backend.py` (Redis stream backend).
- API: `app/api/v1/activity/router.py` exposes list/filter + unread counts, SSE stream, read/dismiss/mark-all receipt endpoints (scope `activity:read`, tenant headers respected).

## How it fits in the app
- Called from other services (auth, conversations, workflows, billing, storage, vector stores, containers, etc.) via `activity_service.record(...)`; action names live in the registry (`auth.login.success`, `conversation.run.completed`, `workflow.run.completed`, `billing.invoice.paid`, `storage.file.uploaded`, `vector.file.synced`, `container.lifecycle`, …).
- Startup wiring (`main.py` lifespan) installs `ActivityService` with `SqlAlchemyActivityEventRepository`, `SqlAlchemyActivityInboxRepository`, and optional Redis stream backend when `ENABLE_ACTIVITY_STREAM=true`.
- Metrics: increments `ACTIVITY_EVENTS_TOTAL{action,status}` on persist and `ACTIVITY_STREAM_PUBLISH_TOTAL{status}` on publish.

## Event lifecycle
1) `record()` validates the `action`/metadata against the registry (unsupported or missing keys raise `ValueError`).  
2) Builds an `ActivityEvent` (UUID id, UTC timestamp, optional actor/object context, `status` default `success`, `source/request_id`, hashed `ip_hash` if provided, optional `user_agent`, metadata).  
3) Persists via the configured `ActivityEventRepository` (defaults to Postgres).  
4) If streaming is enabled, publishes a JSON payload (includes `read_state="unread"`) to the tenant stream key `activity:{tenant_id}`.  
5) Returns the event object for callers to correlate with request logs.

## Inbox / unread state
- `list_events_with_state` decorates events with per-user `read_state` using receipts + a checkpoint for mark-all semantics. When no inbox repo is wired, it still returns events with `read_state="unread"` and `unread_count=len(items)`.
- `mark_read` / `dismiss` upsert a receipt after verifying the event belongs to the tenant; `mark_all_read` writes a checkpoint (`activity_last_seen`) so future unread counts only consider newer events.
- Filtering + pagination: `ActivityEventFilters` cover action/actor/object/status/request_id/time bounds; keyset pagination via opaque cursor.

## Streaming endpoint
- `/api/v1/activity/stream` exposes SSE built on Redis streams. Backlog is replayed first, then it blocks with a keep-alive comment (`:\n\n`) every ~15s. Payload matches the publish JSON with `read_state` preset to `"unread"`.
- Enablement knobs (in `core/settings/activity.py`):  
  - `ENABLE_ACTIVITY_STREAM` (default false)  
  - `ACTIVITY_EVENTS_REDIS_URL` (falls back to `REDIS_URL`)  
  - `ACTIVITY_STREAM_MAX_LENGTH` (default 2048 entries per tenant)  
  - `ACTIVITY_STREAM_TTL_SECONDS` (default 24h; 0 disables expiry)

## Adding a new action
- Add it to `registry.py` with allowed/required metadata keys; keep names hierarchical (e.g., `storage.file.deleted`). Validation will block callers until updated.
- Update any producer service to supply required metadata and, if useful, object context (`object_type/id/name`) and `request_id` for correlation.

## Quick usage
```python
from app.services.activity import activity_service

await activity_service.record(
    tenant_id="t1",
    action="conversation.created",
    actor_id="u1",
    actor_type="user",
    object_type="conversation",
    object_id="c1",
    metadata={"conversation_id": "c1"},
    request_id=request_id,
    ip_address=client_ip,  # hashed before storage
    user_agent=user_agent,
)
```
