# Activity / Audit Log

Last updated: 2025-12-01

## Overview

Tenant-scoped, append-only activity trail that records user/system actions across auth, conversations/agents, workflows, billing bridge, storage/vector/containers. Provides REST listing and optional Redis-backed SSE stream.

## Domain & Storage

- Domain model: `app.domain.activity.ActivityEvent` with actor, object, status, source, request_id, hashed IP, UA, metadata.
- Registry/validation: `app.services.activity.registry.REGISTRY` enforces allowed actions + metadata keys.
- Repository: `SqlAlchemyActivityEventRepository` (`activity_events` table) with keyset pagination (created_at desc, id desc).
- Retention: settings `ACTIVITY_EVENTS_TTL_DAYS`, `ACTIVITY_EVENTS_CLEANUP_BATCH`, `ACTIVITY_EVENTS_CLEANUP_SLEEP_MS`; cleanup script `scripts/cleanup_activity_events.py`.

## API Surface

- `GET /api/v1/activity` — filters: action, actor_id, object_type, object_id, status, request_id, created_before/after; cursor pagination; scope `activity:read` (tenant-scoped).
- `GET /api/v1/activity/stream` — SSE; requires `ENABLE_ACTIVITY_STREAM=true` and Redis stream config.

Response schema: `ActivityEventItem` (id, tenant_id, action, timestamps, actor/object fields, status, request_id, ip_hash, ua, metadata).

## Streaming

- Backend: Redis Streams (`activity:{tenant_id}`) via `RedisActivityEventBackend`.
- Settings: `ENABLE_ACTIVITY_STREAM`, `ACTIVITY_EVENTS_REDIS_URL`, `ACTIVITY_STREAM_MAX_LENGTH`, `ACTIVITY_STREAM_TTL_SECONDS`.

## Instrumentation

- Auth: login success/failure, signup success, logout, password change/reset, service-account issued/revoked.
- Conversations: conversation created + cleared.
- Workflows: run start + completion.
- Billing bridge: subscription updates, invoice paid/failed.
- Storage: file upload/delete.
- Vector: file sync state changes (sync worker).
- Containers: create/delete/bind/unbind lifecycle hooks.

## Metrics

- `activity_events_total{action,result}`
- `activity_stream_publish_total{result}`

## Ops

- Migration: `c3c9b1f4cf29_add_activity_events.py` creates `activity_events` table + indexes.
- Cleanup: run `python -m scripts.cleanup_activity_events --dry-run` then without dry-run; or use `just cleanup-activity-events`.
- Retention defaults: 365 days; adjust via env.

## Notes

- PII: IPs are SHA-256 hashed; metadata is validated/whitelisted; avoid storing secrets. Payloads are JSONB and should stay small.
- Access: default to admins via scope `activity:read`; tenant isolation enforced in queries.
