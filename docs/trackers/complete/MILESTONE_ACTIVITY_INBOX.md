# Milestone: Activity Inbox & Notification Receipts

_Last updated: 2025-12-03_  
**Status:** Completed  
**Owner:** @assistant  
**Domain:** Cross-cutting (Backend + Frontend)  
**ID / Links:** Activity bell read/dismiss UX; Tracker lives at `docs/trackers/current_milestone/MILESTONE_ACTIVITY_INBOX.md`

---

## Objective

Add user-scoped notification receipts (read/dismiss) on top of the immutable activity log, expose badge counts and mark-all-read semantics via the API, and surface controls in the web app’s notification bell so users can manage their feed professionally.

---

## Definition of Done

- Activity inbox persistence: per-user receipts and last-seen checkpoint tables with retention.
- API: mark read/dismiss endpoints, mark-all-read, list returns read_state + unread_count, SSE compatible.
- Frontend: bell dropdown shows unread badge, supports per-item dismiss/read and mark-all-read, uses new API contract.
- Lint/typecheck: `hatch run lint`, `hatch run typecheck`, `pnpm lint`, `pnpm type-check` all pass.
- OpenAPI artifact and generated HeyAPI client updated.
- Tracker updated with progress and changelog.

---

## Scope

### In Scope
- Backend domain, persistence, services, and API routes for activity inbox.
- Frontend notification menu UX and data hooks.
- OpenAPI/export + SDK regeneration.

### Out of Scope
- Email/mobile push notifications.
- Cross-tenant admin dashboards or analytics on reads.

---

## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Immutable audit log + per-user receipts + checkpoint landed. |
| Implementation | ✅ | Backend + frontend + SDK completed. |
| Tests & QA | ✅ | Lint/type-check across API + web. |
| Docs & runbooks | ✅ | Tracker updated. |

---

## Architecture / Design Snapshot

- Keep `activity_events` immutable; overlay per-user state via `activity_event_receipts` (status: unread/read/dismissed) plus `activity_last_seen` checkpoint for efficient “mark all read”.
- API adds read/dismiss endpoints and returns `read_state` + `unread_count`; SSE continues to emit events (default unread).
- Frontend bell uses unread_count from API, optimistic updates for reads/dismissals, and a mark-all-read action; mobile keeps existing visibility rules.

---

## Workstreams & Tasks

### Workstream A – Backend & API

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Domain | Add receipt/checkpoint models + interfaces; wire ActivityService overlay | @assistant | ✅ |
| A2 | Persistence | New tables + Alembic migration; repository impl | @assistant | ✅ |
| A3 | API | List unread_count/read_state + mark read/dismiss/mark-all | @assistant | ✅ |
| A4 | QA | `hatch run lint` / `hatch run typecheck` | @assistant | ✅ |

### Workstream B – Frontend & SDK

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Types/SDK | Update OpenAPI artifact + generated client | @assistant | ✅ |
| B2 | UI/Logic | Bell dropdown: badge from unread_count, per-item read/dismiss, mark-all | @assistant | ✅ |
| B3 | QA | `pnpm lint` / `pnpm type-check` | @assistant | ✅ |

---

## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Tracker | Create milestone tracker | Tracker committed | ✅ | 2025-12-03 |
| P1 – Backend | Domain, repo, migration, API, backend lint/typecheck | New endpoints + green checks | ✅ | 2025-12-05 |
| P2 – Frontend | UI/logic + SDK regen + web checks | Bell UX with read/dismiss working | ✅ | 2025-12-06 |

---

## Dependencies

- Redis available for activity stream (unchanged).
- Postgres migrations must run to add new tables.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Badge counts slow on large tenants | Med | Use checkpoint + indexed queries, limit result sets. |
| Stream/backfill divergence | Low | Default new events to unread; checkpoint set on “mark all read”. |
| Frontend stale SDK | Med | Regenerate client immediately after API change. |

---

## Validation / QA Plan

- Backend: `cd apps/api-service && hatch run lint && hatch run typecheck`.
- Frontend: `cd apps/web-app && pnpm lint && pnpm type-check`.
- Manual: create/dismiss/read events, verify badge counts and SSE updates in bell dropdown.

---

## Rollout / Ops Notes

- Alembic migration required; use `just migrate`.
- No feature flag; always on. Receipts table retention aligned with activity retention.

---

## Changelog

- 2025-12-03 — Backend inbox (receipts, checkpoints, API routes, migration) + lint/typecheck green.
- 2025-12-03 — Frontend bell updated (mark read/dismiss/mark-all, badge from unread_count); OpenAPI + SDK regenerated; lint/type-check green.
- 2025-12-03 — Tracker created and plan agreed.
