<!-- SECTION: Metadata -->
# <Milestone: Short Name>

_Last updated: YYYY-MM-DD_  
**Status:** Planned | In Progress | Completed | Archived  
**Owner:** @handle or team name  
**Domain:** Backend | Frontend | CLI | Infra | Cross-cutting  
**ID / Links:** [Issue/Linear/Jira], [Docs], [Related trackers]

---

<!-- SECTION: Objective -->
## Objective

1–3 sentences on what this milestone is supposed to accomplish.  
Keep it outcome-focused (“what changes in the world when this is done”), not a task list.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

Bullet list of concrete, verifiable end state:

- …
- …
- `hatch run lint` / `pnpm type-check` / tests all pass
- Docs/trackers updated

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- …

### Out of Scope
- …

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ / ⚠️ / ⏳ | … |
| Implementation | ✅ / ⚠️ / ⏳ | … |
| Tests & QA | ✅ / ⚠️ / ⏳ | … |
| Docs & runbooks | ✅ / ⚠️ / ⏳ | … |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

Short summary of the important decisions + links. For example:

- Key decisions (algos, patterns, boundaries, provider choices).
- New modules / packages / tables introduced.
- How this plugs into existing services/agents/CLI.

If there’s a full design doc, just summarize and link it.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

Top-level workstreams, each with its own mini checklist.

### Workstream A – <Name>

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | API | … | … | ✅ |
| A2 | Tests | … | … | ⏳ |

### Workstream B – <Name>

(same table)

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

Use when the milestone is multi-stage or time-based.

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | … | … | ✅ |
| P1 – Impl | … | … | ⏳ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Other milestones / issues that must land first.
- External systems (Stripe, Vault, Redis, etc.).

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| … | Low/Med/High | … |
| … | … | … |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Commands to run (`hatch run lint`, `pytest …`, `pnpm lint`, `pnpm type-check`, Playwright, etc.).
- Any smoke tests or manual checks.
- What “green” looks like.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- How this is enabled/rolled out (flags, envs, CLI commands).
- Migration steps, backfill, or one-time scripts.
- Rollback considerations.

---

<!-- SECTION: Changelog -->
## Changelog

- YYYY-MM-DD — Short note on what landed / changed.
- YYYY-MM-DD — …
