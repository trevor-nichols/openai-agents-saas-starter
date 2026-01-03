<!-- SECTION: Metadata -->
# Milestone: Infra Remediation (Routing + Billing Topology + GCP Services)

_Last updated: 2026-01-03_  
**Status:** Completed  
**Owner:** Platform Foundations  
**Domain:** Infra / Cross-cutting  
**ID / Links:** [docs/ops/hosting-kubernetes.md], [docs/ops/hosting-vps.md], [docs/ops/hosting-gcp.md]

---

<!-- SECTION: Objective -->
## Objective

Restore production-grade infra defaults by enforcing the Next.js BFF routing contract, eliminating
billing replay duplication in multi-replica deployments, and ensuring GCP blueprints are
self-sufficient for first-time applies.

<issue-tracker>
# Issue Tracker: Hosting Coverage + Terraform Export Review

**Scope:** Ops blueprints + Helm/Compose + billing worker topology + release hygiene

---

## Purpose

This tracker captures review findings that must be addressed to meet production-grade SaaS
expectations (clean architecture, predictable boundaries, auditable ops posture). These issues were
identified during the PR review for the hosting coverage + Terraform export + related infra changes.

---

## Issue Index

| ID | Severity | Title | Status |
| --- | --- | --- | --- |
| OPS-001 | High | Kubernetes + VPS routing bypasses Next.js BFF (`/api` routed to FastAPI) | Resolved |
| OPS-002 | Medium | Billing stream replay remains enabled on API pods when dedicated worker is enabled | Resolved |
| OPS-003 | Medium | GCP `enable_project_services` omits required APIs | Resolved |
| OPS-004 | Low | Milestone marked “In Progress” but archived under `complete/` | Resolved |

---

## OPS-001 — Kubernetes + VPS routing bypasses Next.js BFF

**Severity:** High  
**Status:** Resolved  
**Why it matters:** Browser-facing code must route through Next.js API routes so auth cookies are
attached and server-only credentials are used. Routing `/api` directly to FastAPI bypasses that
contract and will break authenticated browser calls in production.

**Evidence**
- `ops/charts/starter/templates/ingress.yaml` routes `/api` → API service.
- `ops/compose/caddy/Caddyfile` routes `/api` → API container.
- `docs/ops/hosting-kubernetes.md` documents `/api` routing to API.

**Impact**
- Authenticated browser traffic fails or becomes inconsistent.
- Security model is violated (cookies not attached, server-side auth not applied).
- Breaks the documented frontend data-access contract.

**Proposed Long-Term Resolution**
- Treat the web app as the sole browser-facing entrypoint.
- Route `/api` to the Next.js web service (BFF), not directly to the API service.
- If a dedicated API hostname is required, reserve it for server-to-server calls or
  update the frontend auth strategy explicitly (not recommended unless needed).

**Acceptance Criteria**
- Ingress and Caddy route `/api` to the web app (Next.js) by default.
- A separate API hostname (optional) is documented and supported without breaking browser auth.
- Hosting docs reflect the BFF contract and include examples for both patterns.

---

## OPS-002 — Billing stream replay enabled on API pods with dedicated worker

**Severity:** Medium  
**Status:** Resolved  
**Why it matters:** When scaling API replicas, any process with
`ENABLE_BILLING_STREAM_REPLAY=true` can replay events on startup, causing duplicates. The runbook
requires the API pods to disable both retry worker and replay when a dedicated worker is used.

**Evidence**
- GCP Terraform disables `ENABLE_BILLING_RETRY_WORKER` but leaves `ENABLE_BILLING_STREAM_REPLAY`
  untouched (default true).
- Helm chart sets `ENABLE_BILLING_RETRY_WORKER=false` for API when worker enabled, but does not
  set replay to false; worker also doesn’t set replay explicitly.
- Compose worker overlay disables retry worker but not replay.

**Impact**
- Duplicate billing replay and possible downstream double-processing.
- Violates the operational guidance in `docs/billing/stripe-runbook.md`.

**Proposed Long-Term Resolution**
- When a dedicated worker is enabled:
  - API pods explicitly set `ENABLE_BILLING_RETRY_WORKER=false` and
    `ENABLE_BILLING_STREAM_REPLAY=false`.
  - Worker pods explicitly set `ENABLE_BILLING_RETRY_WORKER=true` and
    `ENABLE_BILLING_STREAM_REPLAY=true`.
- Apply consistently across Terraform (GCP), Helm, and Compose overlays.

**Acceptance Criteria**
- API pods never replay billing streams when worker is dedicated.
- Worker pods explicitly own replay and retry worker duties.
- Docs align across hosting guides and billing runbook.

---

## OPS-003 — GCP project services list is incomplete

**Severity:** Medium  
**Status:** Resolved  
**Why it matters:** The GCP blueprint depends on Cloud Run, Cloud SQL, Secret Manager, Memorystore,
GCS, IAM, and related APIs. The current `enable_project_services` list only enables compute,
vpcaccess, and servicenetworking, which causes terraform apply failures unless operators pre-enable
services manually.

**Evidence**
- `ops/infra/gcp/locals.tf` only includes compute/vpcaccess/servicenetworking.
- `docs/ops/hosting-gcp.md` lists required services but the blueprint does not enable them.

**Impact**
- First-time deployments fail unless operators manually enable services.
- Contradicts “production-grade blueprint” and “predictable defaults.”

**Proposed Long-Term Resolution**
- Expand `required_project_services` to include all APIs required by the blueprint.
- Provide an override list for advanced operators, and document manual enablement if disabled.
- Reflect the updated contract in the console preset and GCP hosting docs.

**Acceptance Criteria**
- Default terraform apply succeeds with `enable_project_services=true` in a fresh project.
- Docs and wizard presets reflect the full required services list.

---

## OPS-004 — Milestone status inconsistent with archive location

**Severity:** Low  
**Status:** Resolved  
**Why it matters:** Publicly visible artifacts should be internally consistent. A “complete” tracker
should not read “In Progress.”

**Evidence**
- `docs/trackers/complete/2026-1-2/MILESTONE_HOSTING_COVERAGE.md` status is “In Progress.”

**Impact**
- Undercuts auditability and release credibility.

**Proposed Long-Term Resolution**
- Update milestone metadata to “Complete.”

**Acceptance Criteria**
- Archived milestone status matches its directory and completion state.

</issue-tracker>
---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Kubernetes ingress and VPS proxy route `/api` to the Next.js web app by default.
- Optional API host routing is supported and documented without breaking browser auth.
- Dedicated worker topology disables retry + replay on API pods and enables both on workers.
- GCP `enable_project_services` includes all APIs required by the blueprint, with override + docs.
- Milestone metadata + docs updated to reflect completion and correct contracts.
- Required lint/type checks pass for any touched app/package in each phase.
- Tracker updated with phase sign-offs and completion status.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- K8s ingress + VPS Caddy routing to preserve the BFF contract.
- Helm/Compose/Terraform alignment for billing retry + stream replay topology.
- GCP Terraform required services list + related docs/presets.
- Docs + tracker hygiene updates tied to these changes.

### Out of Scope
- Reworking frontend auth to allow direct browser → API calls.
- New hosting providers or multi-region topologies.
- Changes to billing worker implementation (only deployment toggles).

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Decisions locked in issue tracker.
| Implementation | ⚠️ | Infra defaults violate BFF routing + billing replay guidance.
| Tests & QA | ⚠️ | No regression tests for infra defaults; must add validation checks.
| Docs & runbooks | ⚠️ | Hosting docs need routing + billing updates.

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- **Routing contract:** Browser traffic must go through Next.js API routes (BFF) so cookies and
  server-side auth are applied consistently.
- **Billing topology:** Dedicated workers own retry + stream replay; API pods explicitly disable
  both to avoid duplicate processing.
- **GCP bootstrap:** Terraform should enable all required GCP APIs by default; advanced operators
  can override and follow documented manual enablement.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Routing Contract (K8s + VPS)

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Infra | Update Helm ingress to route `/api` to web service by default. | ✅ |
| A2 | Infra | Update Caddy config to route `/api` to web service by default. | ✅ |
| A3 | Docs | Update hosting docs to reflect BFF routing + optional API host. | ✅ |

### Workstream B – Billing Worker Topology Alignment

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Infra | Helm: disable replay on API when worker enabled; enable on worker. | ✅ |
| B2 | Infra | Compose: disable replay on API when worker enabled; enable on worker. | ✅ |
| B3 | Infra | Terraform (GCP): disable replay on API; enable on worker env. | ✅ |
| B4 | Docs | Hosting guides + runbook alignment for retry/replay flags. | ✅ |

### Workstream C – GCP Required Services

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Infra | Expand `required_project_services` list to full API set. | ✅ |
| C2 | Docs | Document override + manual enablement checklist. | ✅ |
| C3 | Console | Ensure presets reflect full service list if exposed. | ✅ |

### Workstream D – Hygiene + Tracker Updates

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | Docs | Fix milestone status metadata in archived tracker. | ✅ |
| D2 | Docs | Update issue tracker and this milestone with phase sign-offs. | ✅ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Decisions locked, tracker created | Issue tracker + milestone drafted | ✅ |
| P1 – Routing | Helm/Caddy changes + docs | Routing updated + docs refreshed + checks run | ✅ |
| P2 – Billing | Retry/replay toggles across infra + docs | Flags aligned + docs updated + checks run | ✅ |
| P3 – GCP Services | Required services list + docs/presets | Terraform + docs updated + checks run | ✅ |
| P4 – Hygiene | Tracker status updates + final validation | All docs/trackers consistent + checks run | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None (self-contained infra + docs updates).

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Breaking auth for browser traffic | High | Preserve BFF routing; document optional API host explicitly. |
| Duplicate billing replays | Med | Explicitly set replay flags in all worker/API templates. |
| GCP apply failures | Med | Enable required APIs by default; document override path. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

Per phase, run the relevant checks for touched areas:

- Infra validation
  - `helm lint ops/charts/starter`
  - `helm template starter ops/charts/starter -f ops/charts/starter/values.prod.yaml`
  - `docker compose -f ops/compose/docker-compose.prod.yml config`
  - `terraform fmt -check -recursive ops/infra`
- Backend (if touched): `cd apps/api-service && hatch run lint` + `hatch run typecheck`
- Console (if touched): `cd packages/starter_console && hatch run lint` + `hatch run typecheck`
- Frontend (if touched): `cd apps/web-app && pnpm lint` + `pnpm type-check`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Routing changes are default-safe; optional API host usage is documented.
- Billing flags are additive; do not require migrations.
- GCP services changes only affect first-time applies or when enablement is toggled.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-03 — Milestone created from issue tracker findings and approved recommendations.
- 2026-01-03 — P1 changes applied; Helm lint + template validated.
- 2026-01-03 — P2 changes applied; Terraform fmt + Compose config checks run; Helm lint + template validated.
- 2026-01-03 — P3 changes applied; Terraform fmt check run for infra updates.
- 2026-01-03 — P4 hygiene updates applied; issue tracker statuses updated.
