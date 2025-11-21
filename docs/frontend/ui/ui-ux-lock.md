## UI/UX Lock

Purpose: freeze UX+UI decisions before implementation so engineers and designers can execute without churn.

### Goals & Non‑Goals
- Goals: clearer hierarchy, faster comprehension, mobile parity, minimal new components, zero feature flags.
- Non‑Goals: rebrand, net-new flows, animation-heavy redesign, design tokens rewrite.

### Principles
- Prioritize primary action per view; demote monitoring/secondary info.
- Consistent spacing (8px base), containers, and surface hierarchy.
- Mobile-first parity for navigation and key actions.
- Reuse existing shadcn/foundation components; refactor styling before inventing new primitives.
- Keep data hooks untouched; changes are layout/visual only.

### Visual System Decisions
- Containers: marketing 1200–1280px; app shell 1080–1200px; gutters `px-6` mobile, `px-10` desktop.
- Spacing scale: 8/12/16/20/24/32px. Section rhythm: `space-y-8` default, `space-y-10` only for marketing hero blocks.
- Typography: h1 32/36 lh 1.2; h2 24/28; h3 18/22; body 15/22; helper 13/20 at 60% opacity.
- Surfaces: `surface-default` (bg), `surface-muted` (cards/tables), `surface-strong` (drawers/hero). Apply subtle borders `border-white/10` and glass only for hero/marketing.
- Buttons: solid = primary, outline = secondary, ghost = tertiary/contextual; icon size 16px; avoid mixed variants in a single row.
- States: unify SkeletonPanel/EmptyState/ErrorState styling; tables and cards share the same empty/error visuals.
- Tables: cap width to container; header weight medium 13px; zebra off; use InlineTag for statuses only.

### Shell & Navigation
- App shell: highlight active link in left rail, add small breadcrumb/title row in top bar, collapse mobile nav into sheet (remove horizontal pill duplication), keep 280px rail on desktop.
- Workspace sublayout: allow optional right drawer; default two-column for content-heavy pages.
- Marketing shell: keep sticky header/footer; add subtle alternating surfaces per section for pacing.
- Auth shell: keep centered card; cap width 520px; add app name + short reassurance copy.

### Page Intent & Layout (per feature)
- Chat Workspace  
  - Purpose: primary conversation hub.  
  - Layout: default two-column (sidebar + chat). Tools/Billing move to right drawer with tabs (Tools | Billing events); tool button in chat toolbar.  
  - Actions: send message, switch agent, view details/export.  
  - States: concise empty chat prompt; loading skeleton for messages; error inline alert under header.  
  - Mobile: sidebar as sheet; drawers full-height.
- Agents Workspace  
  - Purpose: pick agent, chat, review history/tools.  
  - Layout: left catalog (sticky), center chat, “Insights” drawer (tabs: Archive | Tools) opened on demand; default closed to reduce clutter.  
  - Actions: select agent, start chat, open insight drawer.  
  - States: empty catalog and empty archive cards; reuse chat empty state.
- Billing  
  - Overview: two-column with primary (Usage + Events tabs) wide; secondary (Plan snapshot + Invoice) narrow. Stream status tag top-right.  
  - Plans: banner for current plan + grid of plans; plan dialog with sticky footer; highlight price/limits.  
  - Usage & Events pages: keep DataTable; add filter row collapse and consistent empty/error cards.
- Ops / Status  
  - Layout: filter bar collapsible; metrics row light-weight; table full width; “Replay incident” opens right drawer.  
  - Actions: filter, refresh, replay.  
  - States: emphasize permission gates via GlassPanel alerts.
- Account  
  - Tabs keep, but add helper text under triggers; profile/security forms use two-column layout on desktop; sticky save bar for long sections.  
  - Sessions table keeps logout actions grouped in header.
- Settings  
  - Tenant: group cards into two clusters (“Contacts & Webhooks”; “Plan & Flags”); add last-updated chip in header bar.  
  - Signup guardrails: keep tabs; add summary strip above (policy state + quotas); move retry button into banner.
- Dashboard  
  - Keep hero; reduce simultaneous panels—stack KPIs, then (Recent vs Billing) in tabs, then Quick actions.
- Marketing  
  - Vary surfaces per section; add scroll-spy subnav on docs/features; limit to one mid-page CTA and one footer CTA; keep command palette.
- Auth pages  
  - Add concise benefits list under hero; include password policy hint; keep gradients subtle.

### Component Inventory & Status
| Component | Status | Notes |
|-----------|--------|-------|
| SectionHeader | Keep; allow compact variant (sm spacing) | Apply across app; marketing uses large spacing. |
| ConversationSidebar | Keep; add “sheet” variant for mobile | Move to drawer on small screens. |
| ChatInterface | Keep; add sticky composer + max width | Toolbar hosts details/export/tool buttons. |
| AgentSwitcher | Keep; tighten spacing | |
| BillingEventsPanel | Refactor into drawer tab | Shared with chat/tools tab set. |
| ToolMetadataPanel | Refactor into drawer tab | |
| AgentCatalogGrid | Keep; make cards compact | |
| ConversationArchivePanel | Move into Insights drawer | |
| DataTable | Keep; align headers/body typography | |
| StatCard | Keep; lighter helper text | |
| Tabs | Keep; add `aria` labels + helper lines | |
| GlassPanel | Keep; reserve for warnings/ops | |
| InlineTag | Keep; limit to status/badge contexts | |
| SkeletonPanel / EmptyState / ErrorState | Keep; unify padding/border | |
| PlanChangeDialog | Keep; add sticky footer + summary | |
| Marketing CommandDialog/Nav | Keep; ensure mobile parity | |

### Open Questions
- Do we need role-based nav variants (e.g., hide Ops for non-operators) beyond current scope gates?
- Keep command palette on marketing pages or restrict to app shell only?
- Should billing stream status surface in top bar globally or stay local to billing views?
- Any requirement for RTL/localization spacing adjustments?

### Out of Scope for This Lock
- Rebrand/visual identity.
- New animation/motion system.
- Design tokens/theming rewrite.
- Net-new workflows (e.g., audit logs, analytics dashboards).
