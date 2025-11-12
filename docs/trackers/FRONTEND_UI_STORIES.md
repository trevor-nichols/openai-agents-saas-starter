---
title: Frontend UI Story Tracker
owner: Platform Foundations
last_updated: 2025-11-12
status: in-progress
tags:
  - frontend
  - ui
  - roadmap
---

# Frontend UI Story Tracker

## Objective
Capture every remaining high-priority UI story across the marketing, chat, billing, and account surfaces so we can iterate feature-by-feature without losing visibility.

## Scope
- Polish and expand the chat workspace (panels, skeletons, agent/tool metadata) so the core SaaS experience feels production-ready.
- Harden billing + subscription panels with richer layouts, status tags, and data-table usage.
- Complete account/security/service-account flows (profile alerting, password form, sessions table).
- Round out marketing/docs/status/error-boundary surfaces referenced in the UI foundation tracker.

## Story Inventory

| ID | Feature | Story | Components | Status | Owner | Notes |
|----|---------|-------|------------|--------|-------|-------|
| UI-001 | Chat Workspace | Redesign message list + tool drawer with glass panels, InlineTag badges, and skeleton states. | `GlassPanel`, `InlineTag`, `components/ui/states`, `components/ui/sheet` | Done | @platform | Header now surfaces state, bubbles show role/timestamp tags, and tool drawer exposes stats + sorted mappings for the agent. |
| UI-002 | Chat Workspace | Surface conversation details drawer (metadata, export/delete) using `data-table` and `Button` actions. | `Table`, `Button`, `Sheet`, `ErrorState`, `KeyValueList` | Done | @platform | Added `ConversationDetailDrawer` with metadata panel, message table, export/delete controls, and error/skeleton states. |
| UI-003 | Billing Overview | Split billing panel into plan summary, next invoice, usage list, events log using `StatCard`, `Table`, and `GlassPanel`. | `StatCard`, `Table`, `GlassPanel`, `InlineTag` | Done | @platform | New plan snapshot + usage table, invoice card, and event stream list align with the glass system. |
| UI-004 | Account Profile | Show verification alert, tenant metadata, and action buttons inside `GlassPanel` grids. | `GlassPanel`, `Avatar`, `InlineTag`, `Alert`, `Button` | Done | @platform | `features/account/ProfilePanel.tsx` now renders verification alert + tenant snapshot. |
| UI-005 | Account Security | Style password form + MFA CTA with `Form`, `Input`, `Tooltip`, `KeyValueList`. | `Form`, `Input`, `Tooltip`, `KeyValueList`, `SkeletonPanel` | Done | @platform | `features/account/SecurityPanel.tsx` ships password rotation + requirements copy. |
| UI-006 | Sessions / Service Accounts | Render TanStack-powered table with revoke buttons, modal token issuance, and success toasts. | `DataTable`, `Button`, `Dialog`, `Tooltip` | Done | @platform | `SessionsPanel` + `ServiceAccountsPanel` expose revoke + issue flows. |
| UI-007 | Marketing `/docs` | Compose hero/nav, section cards, resource panel, and FAQ accordion using navigation/menu components. | `NavigationMenu`, `Card`, `GlassPanel`, `Accordion`, `InlineTag` | Implemented | @platform | Review copy & design with UI team. |
| UI-008 | Marketing `/status` | Build status cards, uptime stats, incident log table, and alert CTA; reuse `StatCard`, `InlineTag`, `Table`. | `StatCard`, `Table`, `GlassPanel`, `InlineTag` | Implemented | @platform | Need to hook RSS/email endpoints. |
| UI-009 | Error boundaries | Create `error.tsx` for marketing/auth/app route groups that use `ErrorState`, `Button`, and optional `Dialog`. | `ErrorState`, `Button`, `Dialog`, `Sheet` | Done | @platform | Auth, app, and marketing route groups now render branded `ErrorState` components. |
| UI-010 | Component inventory | Log new Shadcn installs in `docs/frontend/ui/components.md` and ensure the nav/header tooling is available. | `navigation-menu`, `dialog`, `command`, `data-table` | Ongoing | @platform | Keep tracker in sync with additions. |

## Next Steps
1. Prioritize `UI-001`/`UI-002` to polish the chat workspace before the other surfaces.
2. Iterate `UI-004`-`UI-006` so the account tab matches the data layer that’s already shipping.
3. Fill any gaps noted in `UI-009`/`UI-010` once error boundaries or new components are required.

## Coordination Notes
- Update this tracker as each story moves to “In progress” or “Done” so stakeholders know exactly which visual threads remain.
- Reference the tracker from `docs/trackers/MILESTONE_FRONTEND_UI_FOUNDATION.md` once these stories land so the milestone fully reflects the work.
