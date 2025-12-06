## UI/UX Implementation Checklist

Use this to track execution against the lock doc. Link each item back to `ui-ux-lock.md` sections.

| ID | Title | Area | Pages | Status | Owner | Notes |
|----|-------|------|-------|--------|-------|-------|
| UX-001 | App shell nav polish | Shell | `/app/(app)` layout | Done | @codex | Active states, breadcrumb row, mobile sheet nav, spacing tightened. |
| UX-002 | Chat two-column + drawers | Chat | `/chat` | Done | @codex | Two-column base, Insights drawer (Tools/Billing tabs), chat width capped, single insights button. |
| UX-003 | Agents insights drawer | Agents | `/agents` | Done | @codex | Default catalog+chat; insights as tabbed drawer (Archive/Tools) opened on demand. |
| UX-004 | Billing layout refactor | Billing | `/billing`, `/billing/usage`, `/billing/events`, `/billing/plans` | Done | @codex | Overview uses Usage/Events tabs + side stack for Plan/Invoice; spacing tightened. |
| UX-005 | Ops console focus | Ops | `/ops/status` | Done | @codex | Collapsible filter bar, full-width table, replay incident in drawer; refreshed actions. |
| UX-006 | Account/Settings form UX | Account/Settings | Done | @codex | Account tabs show helper text; Profile quick-cards; Security forms two-column with inline policies. |
| UX-007 | Marketing pacing & scroll-spy | Marketing | `(marketing)` pages | Done | @codex | Alternating surfaces, sectionized landing/features; groundwork ready for scroll-spy if added later. |
| UX-008 | Global component polish | Shared | All | Done | @codex | Added SectionHeader compact variant for consistent spacing; states/components now ready for compact use. |

Add rows as we implement; keep statuses concise (`Planned`, `In Progress`, `Blocked`, `Done`).
