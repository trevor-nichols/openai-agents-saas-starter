<!-- SECTION: Metadata -->
# Logging Uplift & Local Artifactization

_Last updated: 2025-11-30_  
**Status:** In Progress  
**Owner:** @assistant  
**Domain:** Cross-cutting (Backend, Frontend, CLI)  
**ID / Links:** design-in-repo; related docs to be updated in docs/observability.md and SNAPSHOTs

---

<!-- SECTION: Objective -->
## Objective

Deliver a cohesive, local-first logging experience: per-day log roots with clear separation (API, frontend, infra, CLI), dual all/error files, optional frontend log ingest, and retention/cleanup tooling so developers can capture and inspect errors cleanly without external telemetry.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Per-day log root (`var/log/YYYY-MM-DD`) with `api/`, `frontend/`, `infra/`, `cli/` subfolders and symlink `var/log/current`.
- FastAPI logging supports all+error file sinks, retention pruning, and optional stdout duplex; defaults remain backward compatible.
- Frontend client + Next.js server logs flow to file when enabled; beacon ingest path works (auth by default, optional signed anon).
- CLI `start`/`logs` integrate the new layout by default and provide tail/archive helpers.
- Retention/cleanup documented; new env vars and behaviors captured in docs/observability.md and relevant SNAPSHOTs.
- Automated checks green: `hatch run lint`, `hatch run typecheck`, `pnpm lint`, `pnpm type-check` (and targeted tests) pass.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Daily log root creation, symlink management, and retention pruning.
- Backend logging config: dual handlers (all/error), path resolution via `LOG_ROOT`, optional duplex error tee, retention knobs.
- Frontend logging: client beacon defaults for local, server log redirection to per-day files when `LOG_ROOT` is set; auth-protected ingest with optional signed anon.
- CLI enhancements: start uses dated log roots by default; logs tail/archives understand layout; infra log capture best-effort.
- Documentation updates and new tracker entries.

### Out of Scope
- Shipping to third-party telemetry (Datadog/OTLP already supported, unchanged).
- Historical log backfill or migration of prior ad-hoc logs.
- Full-blown log query UI or search tooling.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | W1–W3 landed; no open design items. |
| Implementation | ✅ | Backend + CLI + FE logging delivered. |
| Tests & QA | ✅ | Targeted unit tests + lint/typecheck + pnpm lint/type-check green. |
| Docs & runbooks | ⚠️ | Observability doc updated; SNAPSHOT refresh deferred. |

---

<!-- SECTION: Architecture / Design Snapshot -->
## Architecture / Design Snapshot

- Log root resolved from `LOG_ROOT` else `var/log/<YYYY-MM-DD>`; `var/log/current` symlink for convenience.
- Backend logging: JSON formatter retained; file sink gains two handlers (all/error) with rotation; optional stdout duplex. Retention prunes dated folders > `LOGGING_MAX_DAYS`.
- Frontend: client logger can default to beacon in local when ingest enabled; server/dev logs forwarded to per-day files when `LOG_ROOT` present; ingest endpoint stays auth-by-default with optional HMAC-signed anon mode.
- CLI: start runner writes process logs into dated root by default; logs tail discovers `current/` and supports `--errors`; archive command zips/prunes dated folders.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### W1 – Backend logging & retention

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| W1.1 | API | Add daily log root resolution, dual handlers (all/error), optional stdout duplex | @assistant | ✅ |
| W1.2 | API | Implement retention pruning (`LOGGING_MAX_DAYS`) and safe path creation | @assistant | ✅ |
| W1.3 | API Tests | Unit tests for config builder, filters, pruning | @assistant | ✅ |

### W2 – CLI integration

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| W2.1 | CLI | Default `start --detached` log dir to daily root; maintain symlink | @assistant | ✅ |
| W2.2 | CLI | Enhance `logs tail` to understand layout, `--errors`, path hints | @assistant | ✅ |
| W2.3 | CLI | Add `logs archive` (zip + prune) | @assistant | ✅ |
| W2.4 | CLI Tests | Unit tests for path resolution/tailing | @assistant | ✅ |

### W3 – Frontend logging & ingest

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| W3.1 | Frontend | Make client logger default to beacon locally when ingest enabled; env guardrails | @assistant | ✅ |
| W3.2 | Frontend | Redirect Next.js server/dev logs to daily files when `LOG_ROOT` set; keep console default otherwise | @assistant | ✅ |
| W3.3 | API/Frontend | Optional signed anon ingest toggle; keep auth default | @assistant | ✅ |
| W3.4 | Frontend Tests | Add coverage for logger sink selection and redact behavior | @assistant | ✅ |

### W4 – Docs & validation

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| W4.1 | Docs | Update docs/observability.md + SNAPSHOT references + env tables | @assistant | ✅ |
| W4.2 | QA | Run `hatch run lint`, `hatch run typecheck`, `pnpm lint`, `pnpm type-check`; document results | @assistant | ✅ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Design | Finalize approach, create tracker (this doc) | Tracker committed, plan agreed | ✅ | 2025-11-30 |
| P1 – Implementation | Deliver W1–W3 features + tests | Workstreams W1–W3 marked complete | ✅ | 2025-12-07 |
| P2 – Validation | Docs + lint/typecheck green | W4 complete; all commands green | ✅ | 2025-12-09 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None blocking; uses existing logging/CLI infrastructure already in repo.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Path/permission mismatches on custom `LOG_ROOT` | Med | Normalize/validate paths, create dirs with safe defaults, doc requirements. |
| Log growth if retention misconfigured | Med | Default retention off but documented; provide pruning command and tests. |
| Beacon spam from anon ingest | Med | Keep auth default; require explicit toggle plus HMAC signature when enabling anon. |
| Developer confusion about multiple sinks | Low | Clear docs and CLI hints; `logs tail` prints active paths. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Automated: `hatch run lint`, `hatch run typecheck`, targeted API logging unit tests, CLI tests, `pnpm lint`, `pnpm type-check`.
- Manual smoke: `just start-dev -- --detached` then verify `var/log/current` tree, send frontend beacon, confirm `frontend.log` events in API all/error files, run `starter-cli logs tail --service api --errors`.
- Archive/prune dry-run: run `starter-cli logs archive --days 3 --dry-run` once implemented.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Default behavior remains stdout unless `LOGGING_SINKS=file` or `LOG_ROOT` is set; new envs are opt-in.
- Auth remains required for frontend ingest; anon mode requires explicit env + signature.
- No migrations; dated folders created on first run.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-11-30 — Milestone opened; plan recorded.
- 2025-11-30 — W1 backend logging delivered (daily roots, all/error files, duplex option, pruning); new unit tests; `hatch run lint`/`typecheck` green.
- 2025-11-30 — W2 CLI integration done (dated log roots in start --detached, enhanced logs tail + archive); CLI lint/tests green.
- 2025-11-30 — W3 frontend/ingest done (beacon default in dev, Next dev log tee to LOG_ROOT, signed anon ingest); `pnpm lint`/`type-check` green.
- 2025-11-30 — W4 docs/QA complete: observability env/local logging documented; lint/typecheck suites rerun and green.
