<!-- SECTION: Metadata -->
# Milestone: Marketing Static Pages

_Last updated: 2025-11-30_  
**Status:** Completed  
**Owner:** @web  
**Domain:** Frontend  
**ID / Links:** [Docs](../templates/MILESTONE_TEMPLATE.md)

---

<!-- SECTION: Objective -->
## Objective

Ship first-class About, Contact, Privacy, and Terms pages under the marketing group so fresh clones have all footer-linked destinations present, styled, and ready for light copy edits.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- `/about`, `/contact`, `/privacy`, `/terms` routes exist under `(marketing)`.
- Shared static-page template renders consistent layout with SectionHeader + GlassPanel.
- Footer links point to the new pages.
- Baseline copy seeded; timestamps present for Privacy/Terms.
- `pnpm lint` and `pnpm type-check` pass.
- Docs/trackers updated.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Add static page content + template.
- Wire routes and footer links.
- Seed copy for legal/privacy placeholders.

### Out of Scope
- Legal review of copy.
- Localization or CMS hookup.
- Additional marketing pages (blog/changelog).

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Simple template using existing UI primitives. |
| Implementation | ✅ | Routes + content shipped. |
| Tests & QA | ✅ | `pnpm lint`, `pnpm type-check` green. |
| Docs & runbooks | ✅ | Tracker added. |

---

<!-- SECTION: Architecture / Design Snapshot -->
## Architecture / Design Snapshot

- New feature module `features/marketing/static-pages` exposes `StaticPage` renderer and content constants.
- Each page imports the shared content and template to keep layout consistent and easy to edit.
- Footer nav now points Company → About/Contact/Privacy/Terms.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Pages & Template

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Frontend | Create static-page template + content constants | @web | ✅ |
| A2 | Frontend | Add routes `/about`, `/contact`, `/privacy`, `/terms` under marketing | @web | ✅ |
| A3 | Frontend | Update footer nav to new destinations | @web | ✅ |

### Workstream B – Validation

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | QA | Run `pnpm lint` and `pnpm type-check` | @web | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Build | Template + routes + footer links | Pages render locally | ✅ | 2025-11-30 |
| P1 – Polish | Copy review, legal signoff (future) | Legal-approved text | ⏳ | TBD |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None for implementation; future legal review depends on counsel.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Placeholder legal copy may differ from required language | Med | Flag for legal review in P1; keep copy concise and editable. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `pnpm lint`
- `pnpm type-check`
- Manual: load `/about`, `/contact`, `/privacy`, `/terms` to verify layout + footer links.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Ships with repo; no flags. Self-hosted users get pages by default.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-11-30 — Initial pages and template added; footer links updated.
